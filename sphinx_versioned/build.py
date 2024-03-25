import os
import fnmatch
import shutil
import pathlib
from sphinx import application
from sphinx.config import Config
from sphinx.errors import SphinxError
from sphinx.cmd.build import build_main

from loguru import logger as log

from sphinx_versioned.sphinx_ import EventHandlers
from sphinx_versioned.lib import TempDir, ConfigInject
from sphinx_versioned.versions import GitVersions, BuiltVersions, PseudoBranch


class VersionedDocs:
    """Handles main build workflow.

    Chronologically, the :meth:`~sphinx_versioned.__init__` first parses the config
    (input parameters via a :class:`dict`) and then handles various paths, like current
    workding directory, source directory and output directory.
    Further, it selects the branches to pre-build/build then finally generates the
    top-level ``index.html`` file.

    Parameters
    ----------
    config : :class:`dict`
    """

    def __init__(self, config: dict, debug: bool = False) -> None:
        self.config = config

        # Read sphinx-conf.py variables
        self.read_conf(config)

        self._versions_to_pre_build = []
        self._versions_to_build = []
        self._failed_build = []

        # Get all versions and make a lookup table
        self._all_branches = self.versions.all_versions
        self._lookup_branch = {x.name: x for x in self._all_branches}

        self._select_exclude_branches()

        # if `--force` is supplied with no `--main-branch`, make the `_active_branch` as the `main_branch`
        if not self.main_branch:
            if self.force_branches:
                self.main_branch = self.versions.active_branch.name
            else:
                self.main_branch = "main"

        if debug:
            return

        self.prebuild()

        # Adds our extension to the sphinx-config
        application.Config = ConfigInject

        self.build()

        # Adds a top-level `index.html` in `output_dir` which redirects to `output_dir`/`main-branch`/index.html
        self._generate_top_level_index()

        print(f"\n\033[92m Successfully built {', '.join([x.name for x in self._built_version])} \033[0m")
        return

    def read_conf(self, config) -> bool:
        if self.local_conf.name != "conf.py":
            self.local_conf = self.local_conf / "conf.py"

        # If default conf.py location fails
        if not self.local_conf.exists():
            log.error(f"conf.py does not exist at {self.local_conf}")
            raise FileNotFoundError(f"conf.py not found at {self.local_conf.parent}")

        log.success(f"located conf.py")

        # Parse sphinx config file i.e. conf.py
        self._sphinx_conf = Config.read(self.local_conf.parent.absolute())
        sv_conf_values = {
            x.replace("sv_", ""): y for x, y in self._sphinx_conf._raw_config.items() if x.startswith("sv_")
        }
        log.error(sv_conf_values)
        log.critical(config)

        master_config = config.copy()
        for x, y in master_config.items():
            if y or x not in sv_conf_values:
                continue
            master_config[x] = sv_conf_values.get(x)
        log.error(master_config)

        for varname, value in master_config.items():
            setattr(self, varname, value)

        # Set additional config for sphinx
        self._additional_args = ()
        self._additional_args += ("-Q",) if self.quite else ()
        self._additional_args += ("-vv",) if self.verbose else ()

        # Initialize GitVersions instance
        self.versions = GitVersions(self.git_root, self.output_dir, self.force_branches)
        return

    def _select_branch(self) -> None:
        if not self.select_branch:
            self._versions_to_pre_build = self._all_branches
            self._exclude_branch()
            return

        for tag in self.select_branches:
            filtered_tags = fnmatch.filter(self._lookup_branch.keys(), tag)
            if filtered_tags:
                self._versions_to_pre_build.extend([self._lookup_branch.get(x) for x in filtered_tags])
            elif self.force_branches:
                log.warning(f"Forcing build for branch `{tag}`, be careful, it may or may not exist!")
                self._versions_to_pre_build.append(PseudoBranch(tag))
            else:
                log.critical(f"Branch not found/selected: `{tag}`, use `--force` to force the build")

        return

    def _exclude_branch(self) -> None:
        if not self.exclude_branch:
            return

        _names_versions_to_pre_build = [x.name for x in self._versions_to_pre_build]
        for tag in self.exclude_branches:
            filtered_tags = fnmatch.filter(_names_versions_to_pre_build, tag)
            for x in filtered_tags:
                self._versions_to_pre_build.remove(self._lookup_branch.get(x))

        return

    def _select_exclude_branches(self) -> list:
        log.debug(f"Instructions to select: `{self.select_branch}`")
        log.debug(f"Instructions to exclude: `{self.exclude_branch}`")
        self._versions_to_pre_build = []

        self._select_branch()

        log.info(f"selected branches: `{[x.name for x in self._versions_to_pre_build]}`")
        return

    def _generate_top_level_index(self) -> None:
        """Generate a top-level ``index.html`` which redirects to the main-branch version specified
        via ``main_branch``.
        """
        if self.main_branch not in [x.name for x in self._built_version]:
            log.critical(
                f"main branch `{self.main_branch}` not found!! / not building `{self.main_branch}`; "
                "top-level `index.html` will not be generated!"
            )
            return

        log.success(f"main branch: `{self.main_branch}`; generating top-level `index.html`")
        with open(self.output_dir / "index.html", "w") as findex:
            findex.write(
                f"""
                <!DOCTYPE html>
                <html>
                <head>
                <meta http-equiv="refresh" content="0; url =
                {self.main_branch}/index.html" />
                </head>
            """
            )
        return

    def _build(self, tag, _prebuild: bool = False) -> bool:
        """Internal build method which actually carries out the pre-build/build transctions
        inside a temporary directory then copy the asset files to the output directory
        if it's not a pre-build.

        Parameters
        ----------
        tag : :class:`git.Branch` or :class:`git.Tag`
            Branch/tag to build.
        _prebuild : :class:`bool`
            Variable to perform/skip pre-builds for selected/all versions.

        Returns
        -------
        :class:`bool`
        """
        # Checkout tag/branch
        self.versions.checkout(tag)
        EventHandlers.CURRENT_VERSION = tag

        with TempDir() as temp_dir:
            log.debug(f"Checking out the tag in temporary directory: {temp_dir}")
            source = str(self.local_conf.parent)
            target = temp_dir
            argv = (source, target)
            argv += self._additional_args
            result = build_main(argv)
            if result != 0:
                raise SphinxError

            if _prebuild:
                log.success(f"pre-build succeded for {tag} :)")
                return True

            output_with_tag = self.output_dir / tag
            if not output_with_tag.exists():
                output_with_tag.mkdir(parents=True, exist_ok=True)

            shutil.copytree(temp_dir, output_with_tag, False, None, dirs_exist_ok=True)
            log.success(f"build succeded for {tag} ;)")
            return True

    def prebuild(self) -> None:
        """Pre-build workflow.

        Method to pre-build the selected/all branches in a temporary environment. Essentially, it builds
        the various selected/all branches with the vanilla sphinx-build method and pass-on the branches
        which ends up successful in vanilla sphinx-build.

        The method carries out the transaction via the internal build method
        :meth:`~sphinx_versioned.build.VersionedDocs._build`.
        """
        if not self.prebuild_branches:
            log.info("No pre-builing...")
            self._versions_to_build = self._versions_to_pre_build
            return

        log.debug("Pre-building...")

        # get active branch
        self._active_branch = self.versions.active_branch

        for tag in self._versions_to_pre_build:
            log.info(f"pre-building: {tag}")
            try:
                self._build(tag, _prebuild=True)
                self._versions_to_build.append(tag)
            except SphinxError:
                log.critical(f"Pre-build failed for {tag}")
            finally:
                # restore to active branch
                self.versions.checkout(self._active_branch.name)

        log.success(f"Prebuilding successful for {', '.join([x.name for x in self._versions_to_build])}")
        return

    def build(self) -> None:
        """Build workflow.

        Method to build the branch in a temporary directory with the modified
        :class:`sphinx_versioned.lib.ConfigInject` and injectes the versions flyout menu to the
        footer or the sidebars.

        The method carries out the transaction via the internal build method
        :meth:`~sphinx_versioned.build.VersionedDocs._build`.
        """
        # get active branch
        self._active_branch = self.versions.active_branch

        self._built_version = []
        EventHandlers.VERSIONS = BuiltVersions(self._versions_to_build, self.versions.build_directory)

        for tag in self._versions_to_build:
            log.info(f"Building: {tag}")
            try:
                self._build(tag.name)
                self._built_version.append(tag)
            except SphinxError:
                log.error(f"build failed for {tag}")
                exit(-1)
            finally:
                # restore to active branch
                self.versions.checkout(self._active_branch)
        return

    pass
