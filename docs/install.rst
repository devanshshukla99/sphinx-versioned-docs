.. _install:

============
Installation
============

The ``sphinx-versioned-docs`` project has the following requirements.

.. _requirements-to-use:

Requirements
============

.. code-block:: markdown

    GitPython>=3.1.31
    loguru>=0.7.0
    setuptools>=66.0.0
    sphinx>=4.6.0
    typer>=0.9.0
    rich

Installing
==========

Now, it can be installed via the following methods:

Installing using pip
--------------------

For this you will require that python3 and `pip <https://pip.pypa.io/en/stable/installation/>`__ are already installed.

.. code-block:: console

    $ pip install sphinx-versioned-docs

Installing using conda
----------------------

In this method, please make sure that anaconda/conda is properly installed:

.. code-block:: console

    $ conda install sphinx-versioned-docs

In order to create a separate environment in conda, follow these instructions:

.. code-block:: console

    $ conda create --name versioned
    $ conda activate versioned
    $ conda install sphinx-versioned-docs

Installing from source
----------------------

This method typically installs that lastest developer version of the package, however, it be used to install stable branches too.

To install the latest developer version:

.. code-block:: console

    $ git clone https://github.com/devanshshukla99/sphinx-versioned-docs
    $ cd sphinx-versioned-docs
    $ pip install .

To install the latest stable release, specified via the ``<release tag>``:

.. code-block:: console

    $ git clone https://github.com/devanshshukla99/sphinx-versioned-docs
    $ cd sphinx-versioned-docs
    $ git checkout <release tag>
    $ pip install .

.. _dev-version:

Installing the developer version
--------------------------------

If you are interested in contributing to the project, then you can setup the developer environment by using:

.. code-block:: console

    $ git clone https://github.com/devanshshukla99/sphinx-versioned-docs
    $ cd sphinx-versioned-docs
    $ pip install -e .[all]
