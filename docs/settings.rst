.. _settings:

========
Settings
========

.. code-block::

    sphinx-versioned [OPTIONS]

The ``sphinx-versioned-docs`` reads options from two sources:

    * From the sphinx ``conf.py`` file.
    * From the provided command-line-arguments.

Configuration File Arguments
============================

Currently, only the ``sv_project_url`` can be set via the ``conf.py``. More options coming in future releases.

.. option:: sv_project_url: <url>

    Setting this variable will make sure that the ``Project home`` is listed on the versions selector badge/menu.

Command Line Arguments
======================

These command line options must be specified when executing the ``sphinx-versioned`` command.

.. option:: -c <directory>, --chdir <directory>

    Change the current working directory.

.. option:: --git-root <directory>

    Path to the git-root of the current repo. Default is the current working directory.

.. option:: -o <directory>, --output <directory>

    Set the output directory.

.. option:: --local-conf <directory>

    Path to the ``conf.py`` for ``sphinx-versioned``. Default is ``conf.py`` at the current working directory.

.. option:: --reset-intersphinx

    Resets intersphinx mapping; acts as a patch for issue `#17 <https://github.com/devanshshukla99/sphinx-versioned-docs/issues/17>`__. Default is `False`.

.. option:: --sphinx-compability

    Adds compatibility for older sphinx versions by monkey patching certain functions. Default is `False`.

.. option:: --prebuild, --no-prebuild

    Pre-build all versions to make sure ``sphinx-build`` has no issues and pass-on the successful builds to ``sphinx-versioned-docs``. Default is `True`.

.. option:: -b <branch names separated by `,` or `|`>, --branches <branch names separated by `,` or `|`>

    Build docs and the version selector menu only for certain tags and branches.

.. option:: -m <branch name>, --main-branch <branch name>

    Specify the main-branch to which the top-level ``index.html`` redirects to. Default is ``main``.

.. option:: --quite, --no-quite

    Silents the output from `sphinx`. Use `--no-quite` to get complete-output from `sphinx`. Default is `True`.

.. option:: -v, --verbose

    Passed directly to sphinx. Specify more than once for more logging in sphinx. Default is `False`.

.. option:: -log <level>, --log <level>

    Provide logging level. Example `--log` debug, Default is ``info``.
    Logging levels can be ``trace``, ``debug``, ``warn``, ``info``, etc.

.. option:: --force

    Force branch selection. Use this option to build detached head/commits. Default is `False`.

.. option:: --help

    Show the help message in command-line.
