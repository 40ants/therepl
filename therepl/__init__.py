import re
import sys
import inspect
import logging

from functools import wraps
from collections.abc import MutableMapping

from IPython.core.magic import Magics, magics_class, line_magic
from IPython.terminal.prompts import Prompts, Token

from .utils import upgrade_objects
from . import rpc
from .log import logger

__version__ = '0.1.1'

shell = None
MAIN_LAYER = {}


def ipython_var(name):
    """Variables which ipython sets on each cell evaluation:

    _, __, ___, _1, _2
    _i, _ii, _iii, _i1, _i2
    """
    return re.match(r'^[_]+$', name) \
        or re.match(r'^_[i]+$', name) \
        or re.match(r'^_i\d+$', name) \
        or re.match(r'^_\d+$', name)


def check():
    return inspect.stack()


def find_changes(before, after):
    """Searches difference between two dicts and returns 3 dicts with:
       * new keys;
       * updated keys;
       * deleted keys;
    """
    new = {}
    updated = {}
    deleted = {}

    for key, value in after.items():
        if not ipython_var(key):
            if key in before:
                prev_value = before[key]
                if prev_value is not value:
                    updated[key] = (prev_value, value)
            else:
                new[key] = value

    for key, value in before.items():
        if not ipython_var(key):
            if key not in after:
                deleted[key] = value

    return new, updated, deleted


def update_namespace(module, new, updated, deleted):
    if module:
        for key, value in new.items():
            setattr(module, key, value)

        for key, (old_value, new_value) in updated.items():
            setattr(module, key, new_value)

            # We also need to update classes of all objects
            # known to the interpreter
            if isinstance(new_value, type):
                upgrade_objects(old_value, new_value)

        for key in deleted:
            if hasattr(module, key):
                delattr(module, key)

    # Now we need to update modules which made "from foo import bar"
    for (old_value, new_value) in updated.values():
        for module in sys.modules.values():
            for key, value in vars(module).items():
                if value is old_value:
                    setattr(module, key, new_value)

        for key, value in MAIN_LAYER.items():
            if value is old_value:
                MAIN_LAYER[key] = new_value


@magics_class
class ModuleManager(Magics):
    def __init__(self, ipython, *args, **kwargs):
        super(ModuleManager, self).__init__(ipython, *args, **kwargs)
        self.debug = False
        
        setattr(ipython,
                'run_cell',
                self.decorate_eval(ipython.run_cell))

    def decorate_eval(self, func):
        """Catches variable changes and stores them into the current module object."""
        @wraps(func)
        def wrapper(code, *args, **kwargs):
            module_globals = self.shell.user_ns

            in_module = kwargs.pop('in_module', None)
            if in_module:
                # TODO: raise an error if module is not found
                module_globals = vars(sys.modules[in_module])

            vars_before = module_globals.copy()

            if in_module:
                exec(code, module_globals)
                result = None
            else:
                result = func(code, *args, **kwargs)

            if not code.startswith('%in '):
                new, updated, deleted = find_changes(vars_before, module_globals)
                update_namespace(
                    self.shell.user_ns.get('__module__'),
                    new,
                    updated,
                    deleted,
                )

                if self.debug:
                    if new:
                        print(f'New vars were introduced: {new}')
                    if updated:
                        print(f'These vars were updated: {updated}')
                    if deleted:
                        print(f'These vars were deleted: {deleted}')

            return result
        return wrapper

    @line_magic('in')
    def in_module(self, name):
        if name in sys.modules:
            if self.debug:
                print(f"Switching from {self.shell.user_ns['__name__']} to {name}")

            self.shell.user_ns.set_module(name)
        else:
            print(f'Module "{name}" not found')

    @line_magic('listen')
    def listen(self, line=None):
        """Starts a http server on 5005 port to enable remote connection from Emacs.
        """
        host = 'localhost'
        port = 5005

        if line:
            if ':' in line:
                host, port = line.split(':', 1)
                port = int(port)
            else:
                port = int(line)
            
        rpc.start(host=host, port=port)
        print(f'Server was started. Load remote-ipython.el in Emacs, and hit C-c C-c on any function definition.')

    @line_magic('debug-module')
    def debug_module(self, *args, **kwargs):
        werkzeug_logger = logging.getLogger("werkzeug")
        if self.debug:
            werkzeug_logger.setLevel(logging.ERROR)
            logger.setLevel(logging.ERROR)
            print(f'Debug mode is off')
        else:
            werkzeug_logger.setLevel(logging.DEBUG)
            logger.setLevel(logging.DEBUG)
            print(f'Debug mode is on')

        self.debug = not self.debug


class ModulePrompts(Prompts):
    def in_prompt_tokens(self):
        return self.add_prefix(super().in_prompt_tokens())

    def out_prompt_tokens(self):
        return self.add_prefix(super().out_prompt_tokens())

    def add_prefix(self, prompt):
        prompt.insert(0, (Token.Prompt, '> '))
        prompt.insert(0, (Token.Prompt, self.shell.user_ns['__name__']))
        return prompt


class Namespace(MutableMapping):
    def __init__(self, initial_dict):
        self._ipython = initial_dict
        self._layer = MAIN_LAYER

    def __getitem__(self, name):
        if name in self._layer:
            return self._layer[name]
        return self._ipython[name]

    def __setitem__(self, name, value):
        if ipython_var(name):
            self._ipython[name] = value
        else:
            # If variable is in the module, then we
            # set it there (unless it is a special ipython's variable
            if name in self._layer:
               self._layer[name] = value
            else:
                if name in self._ipython:
                    self._ipython[name] = value
                else:
                    # If name is not in ipython namespace,
                    # then we'll add it into the module vars
                    self._layer[name] = value

    def copy(self):
        result = self._ipython.copy()
        result.update(self._layer)
        return result

    def __iter__(self):
        names = set(self._ipython)
        names |= set(self._layer)
        return iter(names)

    def __delitem__(self, name):
        if name in self._layer:
            del self._layer[name]
        if name in self._ipython:
            del self._ipython[name]

    def __len__(self):
        names = set(self._ipython)
        names |= set(self._layer)
        return len(names)

    def set_module(self, name):
        new_module = sys.modules[name]

        self._ipython['__name__'] = name
        # We need to store a module here, to update
        # it on subsequent code evaluations.
        # We do updates in update_namespace function
        logger.error(f'Setting __module__ to {new_module}')
        self._ipython['__module__'] = new_module

        if name == '__main__':
            self._layer = MAIN_LAYER
        else:
            self._layer = vars(new_module)


def load_ipython_extension(ipython):
    global shell
    ipython.user_ns = Namespace(ipython.user_ns)
    ipython.prompts = ModulePrompts(ipython)
    shell = ipython

    extension = ModuleManager(ipython)
    ipython.register_magics(extension)
    extension.in_module('__main__')


def unload_ipython_extension(ipython):
    # If you want your extension to be unloadable, put that logic here.
    print('WARNING: Unloading is not supported')
