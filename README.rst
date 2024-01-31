=====================
sphinx-versioned-docs
=====================

|versions| |license|

|build| |CI themes| |docs| |status| |codestyle|

Sphinx extension that allows building versioned docs for self-hosting.
Supported on Linux and macOS.

It works by producing docs for all(specified) branches in separate folders and injects a readthedocs-like version selector menu/badge.

This project is a fork of `Smile-SA/sphinx-versions <https://github.com/Smile-SA/sphinx-versions>`_ with significant changes.

Get started using the `documentation`_

How to use
==========

.. code:: bash

    sphinx-versioned --help

.. code::

    Usage: sphinx-versioned [OPTIONS]

    ╭─ Options ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
    │ --chdir                                        TEXT  Make this the current working directory before running. [default: None]                              │
    │ --output                -O                     TEXT  Output directory [default: docs/_build]                                                              │
    │ --git-root                                     TEXT  Path to directory in the local repo. Default is CWD.                                                 │
    │ --local-conf                                   TEXT  Path to conf.py for sphinx-versions to read config from. [default: docs/conf.py]                     │
    │ --reset-intersphinx     -rI                          Reset intersphinx mapping; acts as a patch for issue #17                                             │
    │ --sphinx-compatibility  -Sc                          Adds compatibility for older sphinx versions by monkey patching certain functions.                   │
    │ --prebuild                    --no-prebuild          Disables the pre-builds; halves the runtime [default: prebuild]                                      │
    │ --branches              -b                     TEXT  Build docs for specific branches and tags [default: None]                                            │
    │ --main-branch           -m                     TEXT  Main branch to which the top-level `index.html` redirects to. [default: main]                        │
    │ --quite                       --no-quite             No output from `sphinx` [default: quite]                                                             │
    │ --verbose               -v                           Passed directly to sphinx. Specify more than once for more logging in sphinx.                        │
    │ --log                   -log                   TEXT  Provide logging level. Example --log debug, default=info [default: info]                             │
    │ --help                                               Show this message and exit.                                                                          │
    ╰───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯

.. |versions| image:: https://img.shields.io/pypi/pyversions/sphinx-versioned-docs.svg?logo=python&logoColor=FBE072
    :target: https://pypi.org/project/sphinx-versioned-docs/
    :alt: Python versions supported

.. |status| image:: https://img.shields.io/pypi/status/sphinx-versioned-docs.svg
    :target: https://pypi.org/project/sphinx-versioned-docs/
    :alt: Package stability

.. |license| image:: https://img.shields.io/pypi/l/sphinx-versioned-docs 
    :target: https://pypi.org/project/sphinx-versioned-docs/
    :alt: License

.. |build| image:: https://github.com/devanshshukla99/sphinx-versioned-docs/actions/workflows/main.yml/badge.svg
    :alt: CI

.. |codestyle| image:: https://img.shields.io/badge/code%20style-black-000000.svg
   :target: https://github.com/psf/black

.. |docs| image:: https://readthedocs.org/projects/sphinx-versioned-docs/badge/?version=latest
    :target: https://sphinx-versioned-docs.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

.. |CI themes| image:: https://github.com/devanshshukla99/sphinx-versioned-docs/actions/workflows/CI-themes.yml/badge.svg
    :alt: CI themes
 
.. _documentation: https://sphinx-versioned-docs.readthedocs.io/en/latest/
