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


Connecting from the Emacs
=========================

* In ipython's repl execute ``%listen`` command.
* Load into your emacs `therepl.el`_.
* With cursor on a function definition, hit ``C-c C-c`` to eval it
  in the ipython. Code will be evaled in the module corresponding to
  the python file.
* To switch REPL into the module of the current file, hit ``C-c v``.
  

Development
===========

To start hacking the repl itself:

* install poetry_ package manager.
* do ``poetry install`` in the repl's folder.
* do ``poetry shell`` and start the ``ipython``.


Roadmap
=======

* Make a emacs minor mode.
* Add proper error handling in RPC protocol.
* Create an extension for PyCharm.

.. _poetry: https://github.com/sdispater/poetry
.. _therepl.el: https://github.com/40ants/therepl/blob/master/therepl.el
