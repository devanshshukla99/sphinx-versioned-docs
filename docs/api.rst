=================
API documentation
=================

Entry application
-----------------

The entry point for the package ``sphinx-versioned-docs`` is through :func:`sphinx_versioned.__main__.main`.
The function is actually a Typer CLI with the various command-line options available.

.. automodule:: sphinx_versioned.__main__
    :members:
    :private-members:
    :show-inheritance:


Building workflow
-----------------

.. automodule:: sphinx_versioned.build
    :members:
    :private-members:
    :show-inheritance:

Sphinx extension
----------------

The sphinx-extension is added by default on running ``sphinx-versioned`` to inject the versions flyout
menu directly to the html files.

.. automodule:: sphinx_versioned.sphinx_
    :members:
    :private-members:
    :show-inheritance:

-------------------------------------------

Utiliies/ Libraries
-------------------

.. automodule:: sphinx_versioned.versions
    :members:
    :private-members:
    :show-inheritance:

.. automodule:: sphinx_versioned.lib
    :members:
    :private-members:
    :show-inheritance:
