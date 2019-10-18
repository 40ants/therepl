=================
 ipython-modules
=================

This is an extension for ipython. It adds following features.

* A command ``%in <module-name>`` allowing to switch current namespace
  to a given python module.
* When you are in the module's namespace, all evals will change this module.
* When a function gets redefined in the module, it also will be redefined
  in all other modules where it was imported to.
* The same is for classes.
* But also all objects of a redefined class will be upgraded, to use a new class.
* This should works (I hope) for parent classes, which are intermediate in the MRO chain.
* Also, a command ``%listen`` is available. It starts a simple RPC server
  allowing you to send functions and classes right from the Emacs (this is the only one IDE
  currently supported.


How to use
==========

* Install: ``pip install ipython_modules``.
* Run ``ipython``.
* Load the extension: ``%load_ext ipython_modules``.
* Switch to a module you want to change:

  .. code:: python



            In [1]: %load_ext ipython_modules

__main__> In [2]: %in os

os> In [3]: def getcwd():
       ...:     return 'Oh really!?'
       ...:

os> In [4]: getcwd()
os> Out[4]: 'Oh really!?'

os> In [5]: %in __main__

__main__> In [6]: import os

__main__> In [7]: os.getcwd()
__main__> Out[7]: 'Oh really!?'
