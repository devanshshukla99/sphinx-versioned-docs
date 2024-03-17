import os

os.environ["GIT_PYTHON_REFRESH"] = "quiet"

import git
import pathlib
from abc import ABC
from loguru import logger as log


class PseudoBranch:
    """Class to generate a branch/pseudo-branch for git detached head/commit.

    Parameters
    ----------
    name : :class:`str`
        Branch/pseudo-branch name.
    """

    def __init__(self, name: str) -> None:
        self.name = name
        return

    def __repr__(self) -> str:
        return self.name

    pass


class _BranchTag(ABC):
    """Abstract base class for getting relative paths of branches and tags as properties."""

    @property
    def branches(self) -> dict:
        """Get the branches and its ``index.html`` location.

        Returns
        -------
        :class:`dict`
        """
        return {
            x: "../" + str(y.relative_to(self.build_directory) / "index.html")
            for x, y in self._branches.items()
        }

    @property
    def tags(self) -> dict:
        """Get the tags and its ``index.html`` location.

        Returns
        -------
        :class:`dict`
        """
        return {
            x: "../" + str(y.relative_to(self.build_directory) / "index.html") for x, y in self._tags.items()
        }

    pass


class GitVersions(_BranchTag):
    """Handles git branches and tags. Builds upon the abstract base class :class:`sphinx_versioned.versions._BranchTag`.

    Initlizes and latches into the git repo.

    Parameters
    ----------
    git_root : :class:`str`
        Git repository root directory.
    build_directory : :class:`str`
        Path of build directory.
    force_branches : :class:`bool`
        This option allows `GitVersions` to treat the detached commits as normal branches.
        Use this option to build docs for detached head/commits.
    """

    def __init__(self, git_root: str, build_directory: str, force_branches: bool) -> None:
        self.git_root = git_root
        self.build_directory = pathlib.Path(build_directory)
        self.force_branches = force_branches

        # for detached head
        self._active_branch = None

        if not self.build_directory.exists():
            self.build_directory.mkdir(parents=True, exist_ok=True)

        self.repo = git.Repo(git_root)
        if self.repo.bare:
            self.repo = git.Repo(os.getcwd())
            if self.repo.bare:
                log.error("The git repository is bare. Add some commits then try again!")
                exit(-1)
        log.success("latched into the git repo")

        self._parse_branches()
        return

    def _parse_branches(self) -> bool:
        """Parse branches and tags into separate variables.

        Collect all branches and tags in `GitVersions.all_versions`.
        Additionally, if the head is detached and `--force` is supplied, then append
        a PseudoBranch representing the detached commit sha.

        Returns
        -------
        :class:`bool`
        """
        self._raw_branches = self.repo.branches
        self._raw_tags = self.repo.tags
        self._branches = {x.name: self.build_directory / x.name for x in self._raw_branches}
        self._tags = {x.name: self.build_directory / x.name for x in self._raw_tags}
        self.all_versions = [*self._raw_tags, *self._raw_branches]

        # check if if the current git status is detached, if yes, and if `--force` is supplied -> append:
        if self.repo.head.is_detached:
            log.warning(f"git head detached {self.repo.head.is_detached}")
            if self.force_branches:
                log.debug("Forcing detached commit into PseudoBranch")
                self.all_versions.append(PseudoBranch(self.repo.head.object.hexsha))

        log.debug(f"Found versions: {[x.name for x in self.all_versions]}")
        return True

    def checkout(self, name, *args, **kwargs) -> bool:
        """git checkout the branch/tag with its ``name``.

        Parameters
        ----------
        name : :class:`str`
            Name of the branch/tag.
        """
        self._active_branch = name
        log.debug(f"git checkout branch/tag: `{name}`")
        return self.repo.git.checkout(name, *args, **kwargs)

    @property
    def active_branch(self, *args, **kwargs):
        """Property to get the currently active branch."""
        if self._active_branch:
            return self._active_branch

        if self.repo.head.is_detached:
            log.warning(f"git head detached: {self.repo.head.is_detached}")
            return PseudoBranch(self.repo.head.object.hexsha)

        return self.repo.active_branch

    pass


class BuiltVersions(_BranchTag):
    """Handles versions to build. Builds upon the abstract base class :class:`sphinx_versioned.versions._BranchTag`.

    Parameters
    ----------
    versions : :class:`list:
        Versions to be build.
    build_directory : :class:`str`
        Path of the build directory.
    """

    def __init__(self, versions: list, build_directory: str) -> None:
        self._versions = versions
        self.build_directory = pathlib.Path(build_directory)

        if not self.build_directory.exists():
            self.build_directory.mkdir(parents=True, exist_ok=True)

        self._parse()
        return

    def _parse(self) -> bool:
        """Parse raw branches/tags in :class:`~sphinx_versioned.versions.GitVersions` instance into separate variables."""
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
