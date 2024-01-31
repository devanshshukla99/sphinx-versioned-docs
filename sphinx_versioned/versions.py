"""Collect and sort version strings."""

import os
import git
import pathlib
from abc import ABC
from loguru import logger as log

os.environ["GIT_PYTHON_REFRESH"] = "quiet"


class _BranchTag(ABC):
    """Abstract Base class for getting branches and tags"""

    @property
    def branches(self) -> dict:
        return {
            x: "../" + str(y.relative_to(self.build_directory) / "index.html")
            for x, y in self._branches.items()
        }

    @property
    def tags(self) -> dict:
        return {
            x: "../" + str(y.relative_to(self.build_directory) / "index.html") for x, y in self._tags.items()
        }

    pass


class GitVersions(_BranchTag):
    """Handles git branches and tags. Builds upon the abstract base class `~sphinx_versioned.versions._BranchTag`."""

    def __init__(self, git_root, build_directory) -> None:
        """
        Initlizes and latches into the git repo.

        Parameters
        ----------
        git_root : `str`
            Git repository root
        build_directory : `str`
            Path of build directory
        """
        self.git_root = git_root
        self.build_directory = pathlib.Path(build_directory)

        # for detached head
        self._active_branch = None

        if not self.build_directory.exists():
            self.build_directory.mkdir(parents=True, exist_ok=True)

        self.repo = git.Repo(git_root)
        if self.repo.bare:
            self.repo = git.Repo(os.getcwd())
            if self.repo.bare:
                log.error("Bare repo")
                exit(-1)
        log.success("latched into the git repo")

        self._parse_branches()
        return

    def _parse_branches(self) -> bool:
        """Parse branches and tags into seperate variables.

        Returns
        -------
        `bool`
        """
        self._raw_branches = self.repo.branches
        self._raw_tags = self.repo.tags
        self._branches = {x.name: self.build_directory / x.name for x in self._raw_branches}
        self._tags = {x.name: self.build_directory / x.name for x in self._raw_tags}
        return True

    def checkout(self, name, *args, **kwargs) -> bool:
        """git checkout a branch/tag with `name`.

        Parameters
        ----------
        name : `str`
            Name of branch/tag.
        """
        self._active_branch = name
        return self.repo.git.checkout(name, *args, **kwargs)

    @property
    def active_branch(self, *args, **kwargs):
        """Property to get active_branch."""
        if self._active_branch:
            return self._active_branch
        return self.repo.active_branch

    pass


class BuiltVersions(_BranchTag):
    """Handles versions to build. Builds upon the abstract base class `~sphinx_versioned.versions._BranchTag`."""

    def __init__(self, versions, build_directory) -> None:
        self._versions = versions
        self.build_directory = pathlib.Path(build_directory)

        if not self.build_directory.exists():
            self.build_directory.mkdir(parents=True, exist_ok=True)

        self._parse()
        return

    def _parse(self) -> bool:
        """Parse raw branches/tags in `_versions` into separate variables."""
        self._raw_tags = []
        self._raw_branches = []

        for tag in self._versions:
            if isinstance(tag, git.TagReference):
                self._raw_tags.append(tag)
            else:
                self._raw_branches.append(tag)

        self._branches = {x.name: self.build_directory / x.name for x in self._raw_branches}
        self._tags = {x.name: self.build_directory / x.name for x in self._raw_tags}
        return True

    pass
