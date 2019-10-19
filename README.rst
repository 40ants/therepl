==========
 The REPL
==========

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

* Install: ``pip install therepl``.
* Run ``ipython``.
* Load the extension: ``%load_ext therepl``.
* Switch to a module you want with ``%in <the-module>`` magic command.
* Eval the code like you want to change:

  .. image:: docs/therepl-demo.gif


Development
===========

To start hacking the repl itself:

* install poetry_ package manager.
* do ``poetry install`` in the repl's folder.
* do ``poetry shell`` and start the ``ipython``.


.. _poetry: https://github.com/sdispater/poetry
