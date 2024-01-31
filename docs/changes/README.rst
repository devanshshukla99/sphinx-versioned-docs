Changelog
=========

This directory contains "news fragments" which are short files that contain a small **ReST**-formatted text that will be added to the next ``CHANGELOG``.

The ``CHANGELOG`` will be read by users, so this description should be aimed to stingray users instead of describing internal changes which are only relevant to the developers.

Make sure to use full sentences in the past or present tense and use punctuation.

Each file should be named like ``<PULL REQUEST>.<TYPE>.rst``, where
``<PULL REQUEST>`` is a pull request number, and ``<TYPE>`` is one of:

* ``breaking``: A change which is not backwards compatible and requires users to change code.
* ``feature``: New user facing features and any new behavior.
* ``bugfix``: Fixes a reported bug.
* ``doc``: Documentation improvement, like rewording an entire session or adding missing docs.
* ``deprecation``: Feature deprecation.
* ``removal``: Feature removal.
* ``trivial``: Fixes a small typo or internal change that might be noteworthy.

For example: ``123.feature.rst`` would have the content::

    The ``my_new_feature`` option is now available for ``my_favorite_function``.
    To use it, write ``np.my_favorite_function(..., my_new_feature=True)``.

Note the use of double-backticks for code.

If you are unsure what pull request type to use, don't hesitate to ask in your
PR.

You can install ``towncrier`` and run ``towncrier --draft`` if you want to get a preview of how your change will look in the final release
notes.

.. note::

    This README was adapted from the numpy and pytest changelog readme under the terms of
    the MIT licence.
