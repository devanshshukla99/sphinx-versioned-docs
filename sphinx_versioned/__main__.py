import os
import typer
import shutil
import pathlib
from sphinx import application
from sphinx.config import Config as SphinxConfig
from sphinx.cmd.build import build_main
from sphinx.errors import SphinxError
from sphinx_versioned.versions import GitVersions, BuiltVersions

from loguru import logger as log

from sphinx_versioned.lib import TempDir
from sphinx_versioned.sphinx_ import EventHandlers


app = typer.Typer()


@app.callback()
def cli(
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Debug logging. Specify more than once for more logging."
    ),
):
    pass


class ConfigInject(SphinxConfig):
    """Inject this extension info self.extensions. Append after user's extensions."""

    def __init__(self, *args):
        super(ConfigInject, self).__init__(*args)
        self.extensions.append("sphinx_versioned.sphinx_")


class VersionedDocs:
    def __init__(self, config) -> None:
        self.config = config
        self._parse_config(config)

        self._versions_to_pre_build = []
        self._versions_to_build = []
        self._failed_build = []
        self._quite = "-Q" if self.quite else None

        self._handle_paths()
        self._get_versions_to_pre_build()
        self._pre_build_versions()

        # Adds our extension to the sphinx-config
        application.Config = ConfigInject

        self._build_versions()
        pass

    def _parse_config(self, config):
        for varname, value in config.items():
            setattr(self, varname, value)
        return True

    def _log_versions(
        self,
        versions,
        msg="found version",
    ) -> bool:
        for tag in versions:
            log.info(f"{msg}: {tag.name}")
        return True

    def _handle_paths(self):
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

    def _get_versions_to_pre_build(self) -> bool:
        self._versions_to_pre_build.extend(self.versions.repo.tags)
        self._versions_to_pre_build.extend(self.versions.repo.branches)
        log.info("Pre-building...")
        return self._log_versions(self._versions_to_pre_build)

    def _prebuild(self, tag):
        # Checkout tag/branch
        self.versions.checkout(tag)
        with TempDir() as temp_dir:
            log.debug(f"Checking out the latest tag in temporary directory: {temp_dir}")
            source = str(self.local_conf.parent)
            target = temp_dir
            argv = (source, target)
            if self._quite:
                argv += (self._quite,)
            result = build_main(argv)
            if result != 0:
                raise SphinxError

            log.success(f"pre-build succeded for {tag} :)")

    def _pre_build_versions(self):
        # get active branch
        self._active_branch = self.versions.active_branch

        for tag in self._versions_to_pre_build:
            log.info(f"pre-building: {tag}")
            try:
                self._prebuild(tag)
                self._versions_to_build.append(tag)
            except SphinxError:
                log.error(f"Pre-build failed for {tag}")
            finally:
                # restore to active branch
                self.versions.checkout(self._active_branch.name)

    def _build(self, tag):
        # Checkout tag/branch
        self.versions.checkout(tag)
        EventHandlers.CURRENT_VERSION = tag

        with TempDir() as temp_dir:
            log.debug(f"Checking out the latest tag in temporary directory: {temp_dir}")
            source = str(self.local_conf.parent)
            target = temp_dir
            argv = (source, target)
            if self._quite:
                argv += (self._quite,)
            result = build_main(argv)
            if result != 0:
                raise SphinxError

            output_with_tag = pathlib.Path(self.output_dir) / tag
            if not output_with_tag.exists():
                output_with_tag.mkdir(parents=True, exist_ok=True)
            shutil.copytree(temp_dir, output_with_tag, False, None, dirs_exist_ok=True)
            log.success(f"build succeded for {tag} ;)")

    def _build_versions(self):
        # get active branch
        self._active_branch = self.versions.active_branch

        self._built_version = []
        self._log_versions(self._versions_to_build, msg="building versions")
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


@app.command("build")
def main(
    chdir: str = typer.Option(
        None, "--chdir", help="Make this the current working directory before running."
    ),
    output_dir: str = typer.Option("docs/_build", "--output", "-O", help="Output directory"),
    git_root: str = typer.Option(
        None, "--git-root", help="Path to directory in the local repo. Default is CWD.", show_default=False
    ),
    local_conf: str = typer.Option(
        "docs/conf.py", "--local-conf", help="Path to conf.py for sphinx-versions to read config from."
    ),
    root_ref: str = typer.Option(
        "main",
        "-r",
        "--root-ref",
        help="The branch/tag at the root of DESTINATION. Will also be in subdir.",
    ),
    show_banner: bool = typer.Option(False, "--show-banner", help="Show a warning banner."),
    quite: bool = typer.Option(True, help="No output from `sphinx`"),
) -> None:
    versioned_docs = VersionedDocs(locals())


if __name__ == "__main__":
    app()
