"""Collect and sort version strings."""

import os

os.environ["GIT_PYTHON_REFRESH"] = "quiet"

import git
import pathlib
from loguru import logger as log


class GitVersions(object):
    def __init__(self, git_root, build_directory) -> None:
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

        self._parse_git()
        pass

    def _generate_dirs(self, branches: list, tags: list):
        return {x: self.build_directory / x for x in branches}, {x: self.build_directory / x for x in tags}

    def _parse_name(self, arr) -> bool:
        return [x.name for x in arr]

    def _parse_git(self) -> bool:
        self._raw_branches = self.repo.branches
        self._raw_tags = self.repo.tags
        self._raw_name_branches = self._parse_name(self._raw_branches)
        self._raw_name_tags = self._parse_name(self._raw_tags)
        return True

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

    def checkout(self, name, *args, **kwargs):
        self._active_branch = name
        return self.repo.git.checkout(name, *args, **kwargs)

    @property
    def active_branch(self, *args, **kwargs):
        if self._active_branch:
            return self._active_branch
        return self.repo.active_branch


class BuiltVersions(GitVersions):
    def __init__(self, versions, git_versions, parse_to_name=True) -> None:
        self._versions = versions
        self._git_versions = git_versions
        self.build_directory = pathlib.Path(git_versions.build_directory)

        if not self.build_directory.exists():
            self.build_directory.mkdir(parents=True, exist_ok=True)

        self._parse()

    def _parse(self) -> bool:
        self._branches = []
        self._tags = []
        for tag in self._versions:
            if tag in self._git_versions._raw_name_tags:
                self._tags.append(tag)
            elif tag in self._git_versions._raw_name_branches:
                self._branches.append(tag)
            else:
                # version doesn't exist in git | but still passing it as tag
                log.debug(f"Version tag: {tag} -- not found in git history, but still passing it.")
                self._tags.append(tag)

        self._branches, self._tags = self._generate_dirs(self._branches, self._tags)
        return True
