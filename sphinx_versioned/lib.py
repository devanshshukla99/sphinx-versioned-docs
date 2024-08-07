"""Common objects used throughout the project."""

import os
import re
import atexit
import shutil
import weakref
import tempfile
import functools

from loguru import logger as log

from sphinx import application
from sphinx.config import Config as SphinxConfig


class ConfigInject(SphinxConfig):
    """Inject this extension into `self.extensions`. Append after user's extensions."""

    def __init__(self, *args):
        super(ConfigInject, self).__init__(*args)
        self.extensions.append("sphinx_versioned.sphinx_")

    pass


class HandledError(Exception):
    """Abort the program."""

    def __init__(self):
        """Constructor."""
        super(HandledError, self).__init__(None)

    def show(self, **_):
        """Error messages should be logged before raising this exception."""
        log.critical("Failure.")

    pass


class TempDir(object):
    """Similar to TemporaryDirectory in Python 3.x but with tuned weakref implementation.

    Parameters
    ----------
    defer_atexit: :class:`bool`
        cleanup() to atexit instead of after garbage collection.
    """

    def __init__(self, defer_atexit=False):
        """Constructor.

        :param bool defer_atexit: cleanup() to atexit instead of after garbage collection.
        """
        self.name = tempfile.mkdtemp("sphinx_versioned")
        if defer_atexit:
            atexit.register(shutil.rmtree, self.name, True)
            return
        try:
            weakref.finalize(self, shutil.rmtree, self.name, True)
        except AttributeError:
            weakref.proxy(self, functools.partial(shutil.rmtree, self.name, True))

    def __enter__(self):
        """Return directory path."""
        return self.name

    def __exit__(self, *_):
        """Cleanup when exiting context."""
        self.cleanup()
        pass

    def cleanup(self):
        """Recursively delete directory."""
        shutil.rmtree(
            self.name,
            onerror=lambda *a: os.chmod(a[1], __import__("stat").S_IWRITE) or os.unlink(a[1]),
        )
        if os.path.exists(self.name):
            raise IOError(17, "File exists: '{}'".format(self.name))

    pass


def mp_sphinx_compatibility() -> bool:
    """
    Monkeypatches :meth:`sphinx.application.Sphinx.add_stylesheet` -> :meth:`sphinx.application.Sphinx.add_css_file`
    to add compatibility for versions using older sphinx
    """
    log.info("Monkeypatching older sphinx app.add_stylesheet -> app.add_css_file")
    application.Sphinx.add_stylesheet = application.Sphinx.add_css_file

    return True


def parse_branch_selection(branches: str) -> tuple:
    """
    Parse the CLI-argument string to either select the branch/tag or exclude it.

    Returns (:class:`None`, :class:`None`), if the input is None.

    Parameters
    ----------
    branches : :class:`str`
        Input CLI-argument.

    Returns
    -------
    select_branches, exclude_branches : :class:`list`, :class:`list`
    """
    if not branches:
        return (None, None)

    select_branches = []
    exclude_branches = []
    for x in re.split(r"\s|,|\|", branches):
        if not x:
            continue
        elif x[0] == "-":
            exclude_branches.append(x[1:])
        elif x[0] == "+":
            select_branches.append(x[1:])
        else:
            select_branches.append(x)

    log.info(f"select branch: {select_branches}")
    log.info(f"exclude branch: {exclude_branches}")
    return (select_branches, exclude_branches)
