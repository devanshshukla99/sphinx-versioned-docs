.. _tutorial:

========
Tutorial
========

This guide will go over the basics of the project.

Make sure that you've already :ref:`installed <install>` it.


Building docs locally
=====================

Before we begin make sure you have some Sphinx docs already in your project. If not, read `First Steps with Sphinx <http://www.sphinx-doc.org/en/stable/tutorial.html>`_ first. If you just want something quick
and dirty you can do the following:

.. code-block:: bash

    sphinx-quickstart docs -p projectname -a author -v version --makefile --no-sep -r version -l en -q
    git checkout -b feature_branch main  # Create new branch from main.
    echo -e "Test\n====\n\nSample Documentation" > docs/index.rst  # Create one doc.
    git add .
    git commit -m "initial"
    sphinx-versioned


Building versioned docs
=======================

By default, ``sphinx-versioned-docs`` will try to build all tags and branches present in the git repo, using the command:

.. code-block:: bash

    sphinx-versioned

However, to build some particular branch(s) and tag(s), they can be specified in the ``--branches`` argument as:

.. code-block:: bash

    sphinx-versioned --branches "main, docs"

This command will build the ``main`` and ``docs`` branches.

After the build has succeded, your docs should be available in `docs/_build/<branch>/index.html` with a "Versions" section in the sidebar.

.. note::

    By default, ``sphinx-versioned-docs`` pre-builds the branches to see which of them fails; but this behaviour can be mitigated using the ``--no-prebuild`` argument.

.. note::

    Use ``--no-quite`` option to get output from the sphinx builder, adjust verbosity using ``-v``
