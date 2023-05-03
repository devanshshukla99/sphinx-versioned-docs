.. _contributing:

=================
How to contribute
=================

Welcome contributors!

Installation
============

In order to contribute to this project you'll need to install the package via source with all dependencies.

.. code:: bash

   python -m pip install -e .[all]

Build and upload a new version of sphinx-versioned-docs
=======================================================

Update the README.rst
---------------------

You need to add a section in the ``README.rst`` for the newly created version (follow the pattern of other versions).


Generate package to distribute
------------------------------

This builds your python project and creates the `dist` directory (among other things).

.. code:: bash

   python3 setup.py sdist bdist_wheel

Upload your package to nexus
----------------------------

.. code:: bash

   twine upload dist/*

After this command, your package is available on  https://pypi.org. Anyone can install it using `pip install sphinx-versioned-docs`.
