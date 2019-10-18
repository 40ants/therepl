import re
import sys
import inspect
import logging

from functools import wraps

from IPython.core.magic import Magics, magics_class, line_magic
from IPython.terminal.prompts import Prompts, Token

from .utils import upgrade_objects
from . import rpc

__version__ = '0.1.0'


PROTECTED_VARS = [
]


def var_should_be_ignored(name):
    return re.match(r'^_i*', name) or name == '_' or re.match(r'^_\d+', name)


def clear(variables):
    """This function clears '__main__' module before variables from
       a new module will be loaded into it.
    """
    for key in list(variables):
        if key not in PROTECTED_VARS and not var_should_be_ignored(key):
            del variables[key]

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
        if not var_should_be_ignored(key):
            if key in before:
                prev_value = before[key]
                if prev_value is not value:
                    updated[key] = (prev_value, value)
            else:
                new[key] = value

    for key, value in before.items():
        if not var_should_be_ignored(key):
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
                    module_globals.get('__module__'),
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
            new_module = sys.modules[name]
            variables = self.shell.user_ns

            if self.debug:
                print(f"Switching from {variables['__name__']} to {new_module.__name__}")

            clear(variables)
            variables.update(vars(new_module))
            variables['__name__'] = name

            # We need to store a module here, to update
            # it on subsequent code evaluations.
            # We do updates in update_namespace function
            variables['__module__'] = new_module

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
        print(f'Server was started. Connect to {host}:{port} now.')

    @line_magic('debug-module')
    def debug_module(self, *args, **kwargs):
        logger = logging.getLogger("werkzeug")
        if self.debug:
            logger.setLevel(logging.ERROR)
            print(f'Debug mode is off')
        else:
            logger.setLevel(logging.DEBUG)
            print(f'Debug mode is on')

        self.debug = not self.debug


class ModulePrompts(Prompts):
    def in_prompt_tokens(self):
        return self.add_prefix(super().in_prompt_tokens())

    def out_prompt_tokens(self):
        # print('Updating OUT 2 primopmt', self.shell)
        return self.add_prefix(super().out_prompt_tokens())

    def add_prefix(self, prompt):
        # print('adding prefix to', prompt)
        prompt.insert(0, (Token.Prompt, '> '))
        prompt.insert(0, (Token.Prompt, self.shell.user_ns['__name__']))
        return prompt


shell = None

def load_ipython_extension(ipython):
    global shell
    # The `ipython` argument is the currently active `InteractiveShell`
    # instance, which can be used in any way. This allows you to register
    # new magics or aliases, for example.
    PROTECTED_VARS.extend(ipython.user_ns)

    ipython.prompts = ModulePrompts(ipython)
    shell = ipython

    extension = ModuleManager(ipython)
    ipython.register_magics(extension)


def unload_ipython_extension(ipython):
    # If you want your extension to be unloadable, put that logic here.
    print('WARNING: Unloading is not supported')
