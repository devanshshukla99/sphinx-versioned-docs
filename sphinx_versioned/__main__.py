import re
import sys
import typer

from loguru import logger as log

from sphinx_versioned.build import VersionedDocs
from sphinx_versioned.sphinx_ import EventHandlers
from sphinx_versioned.lib import mp_sphinx_compatibility

app = typer.Typer(add_completion=False)


@app.command(help="Create sphinx documentation with a version selector menu.")
def main(
    chdir: str = typer.Option(
        None,
        "--chdir",
        help="Make this the current working directory before running.",
    ),
    output_dir: str = typer.Option("docs/_build", "--output", "-O", help="Output directory."),
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
    prebuild: bool = typer.Option(
        True, help="Pre-builds the documentations; Use `--no-prebuild` to half the runtime."
    ),
    branches: str = typer.Option(
        None,
        "-b",
        "--branch",
        help="Build documentation for specific branches and tags.",
    ),
    main_branch: str = typer.Option(
        None,
        "-m",
        "--main-branch",
        help="Main branch to which the top-level `index.html` redirects to. Defaults to `main`.",
        show_default="main",
    ),
    floating_badge: bool = typer.Option(
        False, "--floating-badge", "--badge", help="Turns the version selector menu into a floating badge."
    ),
    quite: bool = typer.Option(
        True, help="Silent `sphinx`. Use `--no-quite` to get build output from `sphinx`."
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Passed directly to sphinx. Specify more than once for more logging in sphinx.",
    ),
    loglevel: str = typer.Option(
        "info", "-log", "--log", help="Provide logging level. Example --log debug, default=info"
    ),
    force_branches: bool = typer.Option(
        False,
        "--force",
        help="Force branch selection. Use this option to build detached head/commits. [Default: False]",
    ),
) -> None:
    """
    Typer application for initializing the ``sphinx-versioned`` build.

    Parameters
    ----------
    chdir : :class:`str`
        Make this the current working directory before running. [Default = `None`]
    output_dir : :class:`str`
        Output directory. [Default = 'docs/_build']
    git_root : :class:`str`
        Path to directory in the local repo. Default is CWD.
    local_conf : :class:`str`
        Path to conf.py for sphinx-versions to read config from.
    reset_intersphinx_mapping : :class:`bool`
        Reset intersphinx mapping; acts as a patch for issue #17
    sphinx_compatibility : :class:`bool`
        Adds compatibility for older sphinx versions by monkey patching certain functions.
    prebuild : :class:`bool`
        Pre-builds the documentations; Use `--no-prebuild` to half the runtime. [Default = `True`]
    branches : :class:`str`
        Build docs for specific branches and tags. [Default = `None`]
    main_branch : :class:`str`
        Main branch to which the top-level `index.html` redirects to. [Default = 'main']
    floating_badge : :class:`bool`
        Turns the version selector menu into a floating badge. [Default = `False`]
    quite : :class:`bool`
        Quite output from `sphinx`. Use `--no-quite` to get output from `sphinx`. [Default = `True`]
    verbose : :class:`bool`
        Passed directly to sphinx. Specify more than once for more logging in sphinx. [Default = `False`]
    loglevel : :class:`str`
        Provide logging level. Example `--log` debug, [Default='info']
    force_branches : :class:`str`
        Force branch selection. Use this option to build detached head/commits. [Default = `False`]

    Returns
    -------
    :class:`sphinx_versioned.build.VersionedDocs`
    """
    logger_format = "| <level>{level: <8}</level> | - <level>{message}</level>"

    log.remove()
    log.add(sys.stderr, format=logger_format, level=loglevel.upper())

    select_branches = []
    exclude_branches = []
    if branches:
        for x in re.split(r"\s|,|\|", branches):
            if not x:
                continue
            elif x[0] == "-":
                exclude_branches.append(x[1:])
            elif x[0] == "+":
                select_branches.append(x[1:])
            else:
                select_branches.append(x)

        log.info(f"select branch: {select_branches}")
        log.info(f"exclude branch: {exclude_branches}")

    EventHandlers.RESET_INTERSPHINX_MAPPING = reset_intersphinx_mapping
    EventHandlers.FLYOUT_FLOATING_BADGE = floating_badge

    if reset_intersphinx_mapping:
        log.warning("Forcing --no-prebuild")
        prebuild = False

    if sphinx_compatibility:
        mp_sphinx_compatibility()

    return VersionedDocs(
        {
            "chdir": chdir,
            "output_dir": output_dir,
            "git_root": git_root,
            "local_conf": local_conf,
            "prebuild_branches": prebuild,
            "select_branches": select_branches,
            "exclude_branches": exclude_branches,
            "main_branch": main_branch,
            "quite": quite,
            "verbose": verbose,
            "force_branches": force_branches,
        }
    )


if __name__ == "__main__":
    app()
