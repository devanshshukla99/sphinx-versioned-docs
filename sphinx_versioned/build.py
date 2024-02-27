import os
import shutil
import pathlib
from sphinx import application
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

    def __init__(self, config: dict) -> None:
        self.config = config
        self._parse_config(config)
        self._handle_paths()

        self._versions_to_pre_build = []
        self._versions_to_build = []
        self._failed_build = []

        # selectively build branches / build all branches
        self._versions_to_pre_build = (
            self._select_specific_branches() if self.select_branches else self._get_all_versions()
        )

        # if `--force` is supplied with no `--main-branch`, make the `_active_branch` as the `main_branch`
        if not self.main_branch:
            if self.force_branches:
                self.main_branch = self.versions.active_branch.name
            else:
                self.main_branch = "main"

        self.prebuild()

        # Adds our extension to the sphinx-config
        application.Config = ConfigInject

        self.build()

        # Adds a top-level `index.html` in `output_dir` which redirects to `output_dir`/`main-branch`/index.html
        self._generate_top_level_index()

        print(f"\n\033[92m Successfully built {', '.join([x.name for x in self._built_version])} \033[0m")
        return

    def _parse_config(self, config: dict) -> bool:
        for varname, value in config.items():
            setattr(self, varname, value)

        self._additional_args = ()
        self._additional_args += ("-Q",) if self.quite else ()
        self._additional_args += ("-vv",) if self.verbose else ()
        return True

    def _handle_paths(self) -> None:
        """Method to handle cwd and path for local config, as well as, configure
        :class:`~sphinx_versioned.versions.GitVersions` and the output directory.
        """
        self.chdir = self.chdir if self.chdir else os.getcwd()
        log.debug(f"Working directory {self.chdir}")

        self.versions = GitVersions(self.git_root, self.output_dir)
        self.output_dir = pathlib.Path(self.output_dir)
        self.local_conf = pathlib.Path(self.local_conf)

        if self.local_conf.name != "conf.py":
            self.local_conf = self.local_conf / "conf.py"

        if not self.local_conf.exists():
            log.error(f"conf.py does not exist at {self.local_conf}")
            raise FileNotFoundError(f"conf.py not found at {self.local_conf.parent}")

        log.success(f"located conf.py")
        return

    def _get_all_versions(self) -> list:
        _all_versions = []
        _all_versions.extend(self.versions.repo.tags)
        _all_versions.extend(self.versions.repo.branches)

        # check if `--force` is supplied, if yes, and if the current git status is detached, append:
        if self.force_branches:
            if self.versions.repo.head.is_detached:
                log.warning(f"git detached {self.versions.repo.head.is_detached}")
                _all_versions.append(PseudoBranch(self.versions.repo.head.object.hexsha))

        # self._log_versions(_all_versions)
        log.debug(f"Found versions: {[x.name for x in _all_versions]}")
        return _all_versions

    def _select_specific_branches(self) -> list:
        log.debug(f"Instructions to select: `{self.select_branches}`")

        _all_versions = {x.name: x for x in self._get_all_versions()}
        _select_specific_branches = []

        for tag in self.select_branches:
            if tag in _all_versions.keys():
                log.info(f"Selecting tag for further processing: {tag}")
                _select_specific_branches.append(_all_versions[tag])
            elif self.force_branches:
                log.warning(f"Forcing build for branch `{tag}`, be careful, it may or may not exist!")
                _select_specific_branches.append(PseudoBranch(tag))
            else:
                log.critical(f"Branch not found: `{tag}`, use `--force` to force the build")

        return _select_specific_branches

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
