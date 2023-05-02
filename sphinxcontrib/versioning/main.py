import os
import sys
import typer
import shutil
import pathlib
from typing import List

from loguru import logger as log

from sphinxcontrib.versioning.git import get_root, GitError
from sphinxcontrib.versioning.lib import Config, HandledError, TempDir
from sphinxcontrib.versioning.routines import (
    build_all,
    gather_git_info,
    pre_build,
    read_local_conf,
)
from sphinxcontrib.versioning.versions import multi_sort, Versions

app = typer.Typer()


@app.callback()
def cli(
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Debug logging. Specify more than once for more logging."
    ),
):
    pass


class VersionedDocs:
    def __init__(self, config) -> None:
        self.config = config
        print(config)
        self._parse_config(config)
        self._handle_paths()
        self._gather_git_remotes()
        self._pre_build()
        pass

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

        try:
            self.git_root = get_root(self.git_root or os.getcwd())
            log.debug(f"git root: {self.git_root}")
        except GitError as exc:
            log.error(exc.message)
            log.error(exc.output)
            exit(-1)

        if self.local_conf:
            self.local_conf = pathlib.Path(self.local_conf)
            if self.local_conf.name != "conf.py":
                self.local_conf = self.local_conf / "conf.py"
        else:
            self.local_conf = pathlib.Path("conf.py")
        if not self.local_conf.exists():
            log.error(f"conf.py does not exist at {self.local_conf}")
            raise FileNotFoundError(f"conf.py not found at {self.local_conf.parent}")
        log.success(f"Located conf.py")
        return True

    def _gather_git_remotes(self):
        log.info("Gathering info about the remote git repository...")
        print("***********************")
        print(self.git_root)
        print(self.local_conf)
        print(self.whitelist_branches)
        print(self.whitelist_tags)
        print("***********************")
        remotes = gather_git_info(
            str(self.git_root),
            str(self.local_conf),
            self.whitelist_branches,
            self.whitelist_tags,
        )
        print("***********************")
        print(remotes)
        print("***********************")
        if not remotes:
            log.error("No docs found in any remote branch/tag. Nothing to do.")
        self.versions = Versions(
            remotes,
            False,
            False,
            False,
            False,
            # sort=config.sort,
            # priority=config.priority,
            # invert=config.invert,
            # pdf_file=config.pdf_file,
        )

        # Get root ref.
        if not self.override_root_main_ref(self.versions.remotes, False):
            log.error(
                "Root ref %s not found in: %s",
                self.root_ref,
                " ".join(r[1] for r in remotes),
            )
            raise HandledError

        # Get banner main ref.
        if not self.show_banner:
            self.banner_greatest_tag = False
            self.banner_main_ref = None
            self.banner_recent_tag = False
        elif not self.override_root_main_ref(self.versions.remotes, True):
            log.warning(
                "Banner main ref %s not found in: %s",
                self.banner_main_ref,
                " ".join(r[1] for r in remotes),
            )
            log.warning("Disabling banner.")
            self.banner_greatest_tag = False
            self.banner_main_ref = None
            self.banner_recent_tag = False
            self.show_banner = False
        else:
            log.info("Banner main ref is: %s", self.banner_main_ref)
        return True

    def _pre_build(self) -> bool:
        # Pre-build.
        log.info("Pre-running Sphinx to collect versions' master_doc and other info.")
        exported_root = pre_build(self.git_root, self.versions, self.root_ref, self.config)
        if self.banner_main_ref and self.banner_main_ref not in [r["name"] for r in self.versions.remotes]:
            log.warning(
                "Banner main ref %s failed during pre-run. Disabling banner.",
                self.banner_main_ref,
            )
            self.banner_greatest_tag = False
            self.banner_main_ref = None
            self.banner_recent_tag = False
            self.show_banner = False
        return True

    def override_root_main_ref(self, remotes, banner):
        greatest_tag = self.banner_greatest_tag if banner else self.greatest_tag
        recent_tag = self.banner_recent_tag if banner else self.recent_tag

        if greatest_tag or recent_tag:
            candidates = [r for r in remotes if r["kind"] == "tags"]
            if candidates:
                banner_main_ref = candidates[0]["name"]
            else:
                flag = "--banner-main-ref" if banner else "--root-ref"
                log.warning(f"No git tags with docs found in remote. Falling back to {flag} value.")

        self.root_ref = candidates[0]["name"]
        ref = banner_main_ref if banner else self.root_ref
        log.info(self.root_ref)
        return ref in [r["name"] for r in remotes]


@app.command("build")
def main(
    chdir: str = typer.Option(
        None, "--chdir", help="Make this the current working directory before running."
    ),
    git_root: str = typer.Option(
        None, "--git-root", help="Path to directory in the local repo. Default is CWD.", show_default=False
    ),
    local_conf: str = typer.Option(
        None, "--local-conf", help="Path to conf.py for sphinx-versions to read config from."
    ),
    root_ref: str = typer.Option(
        "main",
        "-r",
        "--root-ref",
        help="The branch/tag at the root of DESTINATION. Will also be in subdir.",
    ),
    banner_greatest_tag: bool = typer.Option(
        None,
        "-a",
        "--banner-greatest-tag",
        help="Override banner-main-ref to be the tag with the highest version number.",
    ),
    banner_recent_tag: bool = typer.Option(
        None,
        "-A",
        "--banner-recent-tag",
        help="Override banner-main-ref to be the most recent committed tag.",
    ),
    whitelist_branches: List[str] = typer.Option(
        None,
        "-B",
        "--whitelist-branches",
        help="Whitelist branches that match the pattern. Can be specified more than once.",
    ),
    whitelist_tags: List[str] = typer.Option(
        None,
        "-T",
        "--whitelist-tags",
        help="Whitelist tags that match the pattern. Can be specified more than once.",
    ),
    greatest_tag: bool = typer.Option(
        False,
        "--greatest-tag",
        help="Override root-ref to be the tag with the highest version number.",
    ),
    recent_tag: str = typer.Option(
        False,
        "--recent-tag",
        help="Override root-ref to be the most recent committed tag.",
    ),
    show_banner: bool = typer.Option(False, "--show-banner", help="Show a warning banner."),
    destination: str = typer.Option("_build/", "-D", "--dest", help="Destination for the build files"),
) -> None:
    versioned_docs = VersionedDocs(locals())


if __name__ == "__main__":
    app()
