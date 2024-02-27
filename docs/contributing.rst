.. _contributing:

=================
How to contribute
=================

Welcome contributors!

Installation
============

In order to contribute to this project you'll need to install the package via source with all dependencies. Follow :ref:`dev build <dev-version>` for more info.

.. code:: console

   $ python -m pip install -e .[all]

Build and upload a new version of sphinx-versioned-docs
=======================================================

Generate package to distribute
------------------------------

This builds your python project and creates the `dist` directory (among other things).

.. code:: console

   $ python3 setup.py sdist bdist_wheel

Upload your package to nexus
----------------------------

.. code:: console

   $ twine upload dist/*

After this command, your package is available on  https://pypi.org. Anyone can install it using ``pip install sphinx-versioned-docs``.
