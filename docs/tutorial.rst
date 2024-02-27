.. _tutorial:

========
Tutorial
========

This guide will go over the basics of the project.

Make sure that you've already :ref:`installed <install>` it.


Building versioned docs
=======================

Before using the ``sphinx-versioned-docs`` to build a versioned documentation. Make sure you have following things done:

- [x] Project initialized.
- [x] git initialized.
- [x] sphinx initilized.

As soon as the above things are complete, you can perform a sanity check run with sphinx. Just go to the documentation folder (typically ``docs``) and run:

.. code-block:: console

    $ make html

This should generate a preliminary documentation for your project.

Once you are satisfied with sphinx-build and have succesfully :ref:`installed <install>` the package,
you can run the following command to generate the versioned documentation:

.. code-block::

    $ sphinx-versioned

-----------------

If you have problems initializing sphinx and git, then follow these instructions: 

Before we begin make sure you have some Sphinx docs already in your project. If not, read `First Steps with Sphinx <http://www.sphinx-doc.org/en/stable/tutorial.html>`_ first. If you just want something quick
and dirty you can do the following:

.. code-block:: console

    $ sphinx-quickstart docs -p projectname -a author -v version --makefile --no-sep -r version -l en -q
    $ git checkout -b feature_branch main  # Create new branch from main.

    $ echo -e "Test\n====\n\nSample Documentation" > docs/index.rst  # Create one doc.
    $ git add .
    $ git commit -m "initial"

    $ sphinx-versioned

------------------------------

By default, ``sphinx-versioned-docs`` will try to build all tags and branches present in the git repo.
However, to build some particular branch(s) and tag(s), they can be specified in the ``--branches`` argument as:

.. code-block:: console

    $ sphinx-versioned --branches "main, docs"

This command will build the ``main`` and ``docs`` branches.
More such options are available at :ref:`options <settings>`.



After the build has succeded, your docs should be available in ``<output directory>/<branch>/index.html`` with a version selector menu/badge present.

.. note::

    By default, ``sphinx-versioned-docs`` pre-builds the branches to see which of them fails; but this behaviour can be mitigated using the ``--no-prebuild`` argument.

.. note::

    Use ``--no-quite`` option to get output from the sphinx builder, adjust verbosity using ``-v``

---------------------------

Deploy to github pages via github actions
=========================================

A sample github action to build and deploy versioned documentation to github-pages is given:

.. note::

    Note the use of ``fetch-depth: 0`` with ``actions/checkout`` to ensure all branches are available to build during runtime.

.. literalinclude:: ../.github/workflows/static.yml
    :language: yaml
