import re
import os
import sys
import typer
import shutil
import pathlib
from sphinx import application
from sphinx.errors import SphinxError
from sphinx.cmd.build import build_main
from sphinx.config import Config as SphinxConfig
from sphinx_versioned.versions import GitVersions, BuiltVersions

from loguru import logger as log

from sphinx_versioned.lib import TempDir
from sphinx_versioned.sphinx_ import EventHandlers

logger_format = "| <level>{level: <8}</level> | - <level>{message}</level>"

app = typer.Typer(add_completion=False)


class ConfigInject(SphinxConfig):
    """Inject this extension info `self.extensions`. Append after user's extensions."""

    def __init__(self, *args):
        super(ConfigInject, self).__init__(*args)
        self.extensions.append("sphinx_versioned.sphinx_")


class VersionedDocs:
    def __init__(self, config) -> None:
        """Handles main workflow.

        Parameters
        ----------
        config : `dict`
        """
        self.config = config
        self._parse_config(config)
        self._handle_paths()

        self.output_dir = pathlib.Path(self.output_dir)

        self._versions_to_pre_build = []
        self._versions_to_build = []
        self._failed_build = []
        self._additional_args = ()

        self._additional_args += ("-Q",) if self.quite else ()
        self._additional_args += ("-vv",) if self.verbose else ()

        # selectively build branches / build all branches
        self._versions_to_pre_build = (
            self._select_specific_branches() if self.select_branches else self._get_all_versions()
        )
        self._pre_build()

        # Adds our extension to the sphinx-config
        application.Config = ConfigInject

        self.build()

        # Adds a top-level `index.html` in `output_dir` which redirects to `output_dir`/`main-branch`/index.html
        self._generate_top_level_index()

        print(f"\n\033[92m Successfully built {', '.join([x.name for x in self._built_version])} \033[0m")
        return

    def _parse_config(self, config) -> bool:
        for varname, value in config.items():
            setattr(self, varname, value)
        return True

    def _log_versions(
        self,
        versions,
        msg="found version",
    ) -> bool:
        """Logs versions to `stdout`

        Parameters
        ----------
        versions : `~sphinx_versioned.versions.GitVersions`
        mas : `str`

        Return
        ------
        `bool`
        """
        for tag in versions:
            log.info(f"{msg}: {tag.name}")
        return True

    def _handle_paths(self) -> None:
        """Method to handle cwd and path for local config."""
        self.chdir = self.chdir if self.chdir else os.getcwd()
        log.debug(f"Working directory {self.chdir}")

        self.versions = GitVersions(self.git_root, self.output_dir)
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
        self._log_versions(_all_versions)
        return _all_versions

    def _select_specific_branches(self) -> list:
        _all_versions = self._get_all_versions()
        _select_specific_branches = []

        for tag in _all_versions:
            if tag.name in self.select_branches:
                log.info(f"Selecting tag for further processing: {tag.name}")
                _select_specific_branches.append(tag)
        return _select_specific_branches

    def _generate_top_level_index(self) -> None:
        """Generate a top-level ``index.html`` with redirect to the main-branch version."""
        if self.main_branch not in [x.name for x in self._built_version]:
            log.critical(f"main branch {self.main_branch} not found!!")

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
        log.debug(f"main branch '{self.main_branch}' found")
        return

    def _build(self, tag, _prebuild=False) -> bool:
        """Internal build method.

        Parameters
        ----------
        tag : `~git.Branch` or `~git.Tag`
            Branch/tag to build
        _prebuild : `bool`
            Variable to allow/skip pre-building verions

        Returns
        -------
        `bool`
        """
        # Checkout tag/branch
        self.versions.checkout(tag)
        EventHandlers.CURRENT_VERSION = tag

        with TempDir() as temp_dir:
            log.debug(f"Checking out the latest tag in temporary directory: {temp_dir}")
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

    def _pre_build(self) -> None:
        if not self.prebuild:
            log.info("No pre-builing...")
            self._versions_to_build = self._versions_to_pre_build
            return

        log.info("Pre-building...")

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
        """Build workflow."""
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


@app.command()
def main(
    chdir: str = typer.Option(
        None,
        "--chdir",
        help="Make this the current working directory before running.",
    ),
    output_dir: str = typer.Option("docs/_build", "--output", "-O", help="Output directory"),
    git_root: str = typer.Option(
        None,
        "--git-root",
        help="Path to directory in the local repo. Default is CWD.",
        show_default=False,
    ),
    local_conf: str = typer.Option(
        "docs/conf.py",
        "--local-conf",
        help="Path to conf.py for sphinx-versions to read config from.",
    ),
    reset_intersphinx_mapping: bool = typer.Option(
        False,
        "--reset-intersphinx",
        "-rI",
        help="Reset intersphinx mapping; acts as a patch for issue #17",
    ),
    sphinx_compatibility: bool = typer.Option(
        False,
        "--sphinx-compatibility",
        "-Sc",
        help="Adds compatibility for older sphinx versions by monkey patching certain functions.",
    ),
    prebuild: bool = typer.Option(True, help="Disables the pre-builds; halves the runtime"),
    select_branches: str = typer.Option(
        None,
        "-b",
        "--branches",
        help="Build docs for specific branches and tags",
    ),
    main_branch: str = typer.Option(
        "main",
        "-m",
        "--main-branch",
        help="Main branch to which the top-level `index.html` redirects to.",
    ),
    quite: bool = typer.Option(True, help="No output from `sphinx`"),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Passed directly to sphinx. Specify more than once for more logging in sphinx.",
    ),
    loglevel: str = typer.Option(
        "info", "-log", "--log", help="Provide logging level. Example --log debug, default=info"
    ),
) -> None:
    if select_branches:
        select_branches = re.split(",|\ ", select_branches)

    EventHandlers.RESET_INTERSPHINX_MAPPING = reset_intersphinx_mapping

    if reset_intersphinx_mapping:
        log.error("Forcing --no-prebuild")
        prebuild = False

    if sphinx_compatibility:
        """
        Monkeypatching `sphinx.application.Sphinx.add_stylesheet` -> `sphinx.application.Sphinx.add_stylesheet`
        to add compatibility for versions using older sphinx
        """
        log.info("Monkeypatching older sphinx app.add_stylesheet -> app.add_css_file")
        application.Sphinx.add_stylesheet = application.Sphinx.add_css_file

    log.remove()
    log.add(sys.stderr, format=logger_format, level=loglevel.upper())
    return VersionedDocs(locals())


if __name__ == "__main__":
    app()
