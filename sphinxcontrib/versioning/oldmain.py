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


@app.command()
def build(
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
    show_banner: bool = typer.Option(False, "--show-banner", help="Show a warning banner."),
    destination: str = typer.Option("_build/", "-D", "--dest", help="Destination for the build files"),
):
    def override_root_main_ref(remotes, banner):
        greatest_tag = banner_greatest_tag  # if banner else greatest_tag
        recent_tag = banner_recent_tag  # if banner else recent_tag

        if greatest_tag or recent_tag:
            candidates = [r for r in remotes if r["kind"] == "tags"]
            if candidates:
                multi_sort(candidates)
                banner_main_ref = candidates[0]["name"]
            else:
                flag = "--banner-main-ref" if banner else "--root-ref"
                log.warning(f"No git tags with docs found in remote. Falling back to {flag} value.")

        log.info(root_ref)
        ref = banner_main_ref if banner else root_ref
        root_ref = candidates[0]["name"]
        return ref in [r["name"] for r in remotes]

    print(chdir)
    print(whitelist_branches)
    print(whitelist_tags)
    print(destination)

    destination = pathlib.Path(destination)
    if not destination.exists():
        log.debug(f"Destination [{destination}] does not exist; making...")
        destination.mkdir()

    if chdir:
        os.chdir(chdir)
        log.debug(f"Working directory {chdir}")
    else:
        chdir = os.getcwd()

    try:
        git_root = get_root(git_root or os.getcwd())
        log.debug(f"git root: {git_root}")
    except GitError as exc:
        log.error(exc.message)
        log.error(exc.output)
        exit(-1)

    if local_conf:
        local_conf = pathlib.Path(local_conf)
        if local_conf.name != "conf.py":
            local_conf = local_conf / "conf.py"
    else:
        local_conf = pathlib.Path("conf.py")
    if not local_conf.exists():
        log.error(f"conf.py does not exist at {local_conf}")
        raise FileNotFoundError(f"conf.py not found at {local_conf.parent}")
    log.success(f"Located conf.py")

    log.info("Gathering info about the remote git repository...")
    print("***********************")
    print(git_root)
    print(local_conf)
    print(whitelist_branches)
    print(whitelist_tags)
    print("***********************")
    remotes = gather_git_info(
        str(git_root),
        str(local_conf),
        whitelist_branches,
        whitelist_tags,
    )
    print("***********************")
    print(remotes)
    print("***********************")
    if not remotes:
        log.error("No docs found in any remote branch/tag. Nothing to do.")
    versions = Versions(
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
    if not override_root_main_ref(versions.remotes, False):
        log.error(
            "Root ref %s not found in: %s",
            root_ref,
            " ".join(r[1] for r in remotes),
        )
        raise HandledError

    # Get banner main ref.
    if not show_banner:
        banner_greatest_tag = False
        banner_main_ref = None
        banner_recent_tag = False
    elif not override_root_main_ref(versions.remotes, True):
        log.warning(
            "Banner main ref %s not found in: %s",
            banner_main_ref,
            " ".join(r[1] for r in remotes),
        )
        log.warning("Disabling banner.")
        banner_greatest_tag = False
        banner_main_ref = None
        banner_recent_tag = False
        show_banner = False
    else:
        log.info("Banner main ref is: %s", banner_main_ref)

    # Pre-build.
    log.info("Pre-running Sphinx to collect versions' master_doc and other info.")
    exported_root = pre_build(git_root, versions, root_ref)
    if banner_main_ref and banner_main_ref not in [r["name"] for r in versions.remotes]:
        log.warning(
            "Banner main ref %s failed during pre-run. Disabling banner.",
            banner_main_ref,
        )
        banner_greatest_tag = (False,)
        banner_main_ref = (None,)
        banner_recent_tag = (False,)
        show_banner = (False,)

    # Build.
    build_all(exported_root, destination, versions, root_ref)

    # Cleanup.
    log.debug("Removing: %s", exported_root)
    shutil.rmtree(exported_root)


if __name__ == "__main__":
    app()
