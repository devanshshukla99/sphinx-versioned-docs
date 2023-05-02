import os
import sys
import typer
import shutil
import pathlib
from git import Repo
from typing import List
from sphinx import application, locale
from sphinx.config import Config as SphinxConfig
from sphinx.cmd.build import build_main, make_main
from sphinx.errors import SphinxError
from sphinxcontrib.versioning.versions import GitVersions

from loguru import logger as log

from sphinxcontrib.versioning.lib import HandledError, TempDir
from sphinxcontrib.versioning.versions import multi_sort, Versions
from sphinxcontrib.versioning.nailsphinx_ import CLICK_COMMAND, EventHandlers


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
        self.extensions.append("sphinxcontrib.versioning.nailsphinx_")


class VersionedDocs:
    def __init__(self, config) -> None:
        self.config = config
        print(config)
        CLICK_COMMAND = typer.main.get_command(app)
        self._versions_to_build = []

        self._parse_config(config)
        self._handle_paths()
        self._patch()
        self._get_versions_to_build()
        self._build_all_version()
        # self._gather_git_remotes()
        # self._pre_build()
        pass

    def _patch(self):
        # Adds our extension to the sphinx-config
        application.Config = ConfigInject

    def _parse_config(self, config):
        for varname, value in config.items():
            setattr(self, varname, value)
        return True

    def _handle_paths(self):
        self.destination = pathlib.Path(self.destination)
        if not self.destination.exists():
            log.debug(f"Destination [{self.destination}] does not exist; making...")
            self.destination.mkdir()

        if self.chdir:
            os.chdir(self.chdir)
        else:
            self.chdir = os.getcwd()
        log.debug(f"Working directory {self.chdir}")

        self.versions = GitVersions(self.git_root, self.output_dir)
        EventHandlers.VERSIONS = self.versions

        self.local_conf = pathlib.Path(self.local_conf)
        if self.local_conf.name != "conf.py":
            self.local_conf = self.local_conf / "conf.py"
        if not self.local_conf.exists():
            log.error(f"conf.py does not exist at {self.local_conf}")
            raise FileNotFoundError(f"conf.py not found at {self.local_conf.parent}")
        log.success(f"Located conf.py")
        return True

    def _checkout_and_build(self, tag):
        # Checkout tag
        self.versions.checkout(tag.name)
        EventHandlers.CURRENT_VERSION = tag.name

        with TempDir() as temp_dir:
            log.debug(f"Checking out the latest tag in temporary directory: {temp_dir}")
            source = str(self.local_conf.parent)
            target = temp_dir
            argv = (source, target)
            result = build_main(argv)
            print("##########################################################################")
            print(result)
            if result != 0:
                raise SphinxError
            output_with_tag = pathlib.Path(self.output_dir) / tag.name
            if not output_with_tag.exists():
                output_with_tag.mkdir(parents=True, exist_ok=True)
            shutil.copytree(temp_dir, output_with_tag, False, None, dirs_exist_ok=True)
            log.success("build succeded ;)")
    
    def _get_versions_to_build(self):
        self._versions_to_build.extend(self.versions.repo.tags)
        self._versions_to_build.extend(self.versions.repo.branches)

    def _build_all_version(self):
        log.debug(f"Tags: {self.versions.repo.tags}")
        # self.versions = Versions(self.git.tags)

        # get active branch
        self._active_branch = self.versions.active_branch

        self._built_version = []
        for tag in self._versions_to_build:
            log.info(f"Building: {tag}")
            try:
                self._checkout_and_build(tag)
            except SphinxError:
                self._built_version.append(tag)
                log.error(f"build failed for {tag}")

        # restore to active branch
        self.versions.checkout(self._active_branch.name)


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
    destination: str = typer.Option("_build/", "-D", "--dest", help="Destination for the build files"),
) -> None:
    versioned_docs = VersionedDocs(locals())


if __name__ == "__main__":
    app()
