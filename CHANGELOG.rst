1.2 (2024-02-01)
=========================================

Deprecations and Removals
-------------------------

- Removed ``--list-branches`` and ``-l`` arg in cli-app. (`#39 <https://github.com/devanshshukla99/sphinx-versioned-docs/pull/39>`__)


Features
--------

- Added `sphinx_compatibility` kwarg to help generate documentations for versions using deprecated function.
  Currently, monkey patching `app.add_stylesheet` -> `app.add_css_file`. (`#33 <https://github.com/devanshshukla99/sphinx-versioned-docs/pull/33>`__)
- Generates a top-level index page which redirect to the index page of the main branch.
  By default, the main branch is "main" / can be changed using the `--main-branch` kwarg. (`#34 <https://github.com/devanshshukla99/sphinx-versioned-docs/pull/34>`__)


Bug Fixes
---------

- Hotfix for #17. It solves by resetting the intersphinx mapping var for the next execution. Forces ``--no-prebuild``. (`#25 <https://github.com/devanshshukla99/sphinx-versioned-docs/pull/25>`__)
- Fixed version menu flyout script in `sphinx_rtd_theme`. Not entirely sure why but somehow `sphinx_rtd_theme` doesn't require the flyout script anymore. (`#27 <https://github.com/devanshshukla99/sphinx-versioned-docs/pull/27>`__)
- Fixed a bug where versions menu was working from the top-level however, it used fail when accessing other versions from deep links. (`#37 <https://github.com/devanshshukla99/sphinx-versioned-docs/pull/37>`__)


1.1 (2023-05-19)
================

Backwards Incompatible Changes
------------------------------

- Migrating call command from ``sphinx-versioned build`` to just ``sphinx-versioned`` for simplicity. (`#21 <https://github.com/devanshshukla99/sphinx-versioned-docs/pull/21>`__)


Features
--------

- Added ``--list-branches`` and ``-l`` arg in cli-app. (`#22 <https://github.com/devanshshukla99/sphinx-versioned-docs/pull/22>`__)


1.0 (2023-05-03)
================

Backwards Incompatible Changes
------------------------------

- Breaking previously forked functionality of ``sphinx-versions``. (`#5 <https://github.com/devanshshukla99/sphinx-versioned-docs/pull/5>`__)
- The package will now be called via ``sphinx-versioned``. (`#6 <https://github.com/devanshshukla99/sphinx-versioned-docs/pull/6>`__)
- Removed windows from the list of compatible platforms due to an issue with ``pwd``, which is probably a dependency of ``gitpython``. (`#15 <https://github.com/devanshshukla99/sphinx-versioned-docs/pull/15>`__)


Features
--------

- Added support for ``sphinx-astropy`` theme. (`#10 <https://github.com/devanshshukla99/sphinx-versioned-docs/pull/10>`__)
- Pre-builing all tags and branches to list only succesful builds in the versions menu. It will double the build time; however, it can be avoided by disabling the pre-building using ``--no-prebuild`` arg or by specifically selecting the tag/branch names via ``--branches`` argument, note that it takes a ``str`` argument of the form "main, master". (`#12 <https://github.com/devanshshukla99/sphinx-versioned-docs/pull/12>`__)


Bug Fixes
---------

- Fixed click 8+ compatibility and ``add_css_file``. (`#1 <https://github.com/devanshshukla99/sphinx-versioned-docs/pull/1>`__)
- Fixed version menu loading issue with ``sphinx_rtd_theme``. (`#11 <https://github.com/devanshshukla99/sphinx-versioned-docs/pull/11>`__)


Added/Improved Documentation
----------------------------

- Updated documentation with respect to new functionalities. (`#6 <https://github.com/devanshshukla99/sphinx-versioned-docs/pull/6>`__)
- Updated documentation, added ``docs/install.rst``, ``docs/api.rst`` and more. (`#16 <https://github.com/devanshshukla99/sphinx-versioned-docs/pull/16>`__)


Trivial/Internal Changes
------------------------

- Added worflows to maintain and verify codestyle using ``black``. (`#2 <https://github.com/devanshshukla99/sphinx-versioned-docs/pull/2>`__)
- Added CI infrastructure to test the package against an empty package created using sphinx-quickstart. (`#4 <https://github.com/devanshshukla99/sphinx-versioned-docs/pull/4>`__)
- Added tests to verify the package against ``sphinx_rtd_theme``, ``astropy_sphinx_theme`` and ``alabaster`` themes. (`#13 <https://github.com/devanshshukla99/sphinx-versioned-docs/pull/13>`__)
- Migrating to ``towncrier`` for changelog management. (`#19 <https://github.com/devanshshukla99/sphinx-versioned-docs/pull/19>`__)
