import re
import sys
import inspect
from functools import wraps

from IPython.core.magic import Magics, magics_class, line_magic
from IPython.terminal.prompts import Prompts, Token

from .utils import upgrade_objects

__version__ = '0.1.0'


PROTECTED_VARS = [
]

def clear(variables):
    for key in list(variables):
        if key not in PROTECTED_VARS:
            del variables[key]

def check():
    return inspect.stack()


def var_should_be_ignored(name):
    return re.match(r'^_i*', name) or name == '_' or re.match(r'^_\d+', name)


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


def update_namespace(namespace, new, updated, deleted):
    if '__module__' in namespace:
        module = namespace['__module__']

        for key, value in new.items():
            setattr(module, key, value)

        for key, (old_value, new_value) in updated.items():
            setattr(module, key, new_value)

            # We also need to update classes of all objects
            # known to the interpreter
            if isinstance(new_value, type):
                upgrade_objects(old_value, new_value)

        for key in deleted:
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
            vars_before = self.shell.user_ns.copy()
            result = func(code, *args, **kwargs)
            vars_after = self.shell.user_ns

            if not code.startswith('%in '):
                new, updated, deleted = find_changes(vars_before, vars_after)
                update_namespace(self.shell.user_ns, new, updated, deleted)

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

            stack = inspect.stack()
            stack_level = 4 # probably we should go over all frames searching
                            # a one with 'Out' variable in it's globals
            variables = stack[stack_level].frame.f_globals

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

    @line_magic('module-debug')
    def module_debug(self, *args, **kwargs):
        if self.debug:
            print(f'Debug mode is off')
        else:
            print(f'Debug mode is on')

        self.debug = not self.debug


class ModulePrompts(Prompts):
    def in_prompt_tokens(self):
        print('Updating IN primopmt')
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
