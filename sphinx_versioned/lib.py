"""Common objects used throughout the project."""

import os
import atexit
import shutil
import weakref
import tempfile
import functools

from loguru import logger as log


class HandledError(Exception):
    """Abort the program."""

    def __init__(self):
        """Constructor."""
        super(HandledError, self).__init__(None)

    def show(self, **_):
        """Error messages should be logged before raising this exception."""
        log.critical("Failure.")


class TempDir(object):
    """Similar to TemporaryDirectory in Python 3.x but with tuned weakref implementation."""

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
