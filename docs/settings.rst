.. _settings:

========
Settings
========

.. code-block:: console

    $ sphinx-versioned [OPTIONS]

The ``sphinx-versioned-docs`` reads options from two sources:

    * From the sphinx ``conf.py`` file.
    * From the provided command-line-arguments.

Configuration File Arguments
============================

.. option:: sv_project_url: <url>

    Setting this variable will make sure that the ``Project home`` is listed on the versions selector badge/menu.

.. option:: sv_select_branch

    Select any particular branches/tags to build.
    The branch/tag names can be separated by ``,`` or ``|``.

    Selecting a branch will always take precedence over excluding one.

    Example: ``sv_select_branch=["main", "v2.0"]``
    The option above will build ``main``, ``v2.0`` and will skip all others.

.. option:: sv_exclude_branch

    Exclude any particular branches/tags from building workflow.
    The branch/tag names can be separated by ``,`` or ``|``.

    Selecting a branch will always take precedence over excluding one.

    Example: ``sv_exclude_branch=["v1.0"]``
    The option above will exclude ``v1.0`` and will build all others.

.. option:: sv_main_branch

    Specify the main-branch to which the top-level ``index.html`` redirects to. Default is ``main``.

.. option:: sv_quite

    Silents the output from `sphinx`. Use `--no-quite` to get complete-output from `sphinx`. Default is `True`.

.. option:: sv_verbose

    Passed directly to sphinx. Specify more than once for more logging in sphinx. Default is `False`.

.. option:: sv_force_branches

    Force branch selection. Use this option to build detached head/commits. Default is `False`.

.. option:: sv_floating_badge

    Turns the version selector menu into a floating badge. Default is `False`.

.. option:: sv_reset_intersphinx

    Resets intersphinx mapping; acts as a patch for issue `#17 <https://github.com/devanshshukla99/sphinx-versioned-docs/issues/17>`__. Default is `False`.

.. option:: sv_sphinx_compability

    Adds compatibility for older sphinx versions by monkey patching certain functions. Default is `False`.


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

.. option:: -b <branch names>, --branch <branch names>

    Build documentation for selected branches and tags.
    The branch/tag names can be separated by ``,`` or ``|`` and supports regex.

    Example: ``sphinx-versioned --branch="main, v1.0, v2.0"``
    
    ``sphinx-versioned --branch="main, -v*"``

.. option:: -m <branch name>, --main-branch <branch name>

    Specify the main-branch to which the top-level ``index.html`` redirects to. Default is ``main``.

.. option:: --floating-badge, --badge

    Turns the version selector menu into a floating badge. Default is `False`.

.. option:: --ignore-conf
 
    Ignores conf.py configuration file arguments for sphinx-versioned-docs.

    .. warning::
        conf.py will still be used in sphinx!

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
