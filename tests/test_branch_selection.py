import os
import pytest
import pathlib
from bs4 import BeautifulSoup as bs
from sphinx_versioned.build import VersionedDocs
from sphinx_versioned.lib import parse_branch_selection


VERSIONS_SUPPOSED = {
    "v1.0": [
        "index.html",
    ],
    "main": ["index.html", "example.html", "code_ref/api_ref/example2.html"],
}
BASEPATH = pathlib.Path(os.getcwd()) / "docs"
OUTPATH = BASEPATH / "_build"


@pytest.mark.parametrize(
    "branches, select, exclude",
    [
        ("main,v1.0", ["main", "v1.0"], []),
        ("-v2.0", [], ["v2.0"]),
        ("main,-v1.0, v2.0", ["main", "v2.0"], ["v1.0"]),
        ("-main,+v1.0, -v2.0", ["v1.0"], ["main", "v2.0"]),
    ],
)
def test_parse_branch_selection(branches, select, exclude):
    parsed_select, parsed_exclude = parse_branch_selection(branches)
    assert parsed_select == select
    assert parsed_exclude == exclude


@pytest.mark.parametrize(
    "branches, select, exclude",
    [
        ("main,v*", ["main", "v1.0", "v2.0"], []),
        ("-v2.*", ["main", "v1.0"], ["v2.0"]),
        ("-v*", ["main"], ["v1.0", "v2.0"]),
    ],
)
def test_parse_branch_selection_regex(branches, select, exclude):
    parsed_select, parsed_exclude = parse_branch_selection(branches)

    ver = VersionedDocs(
        chdir=".",
        output_dir=OUTPATH,
        git_root=BASEPATH.parent,
        local_conf="docs/conf.py",
        config={
            "quite": False,
            "verbose": True,
            "main_branch": "main",
            "force_branches": True,
            "select_branch": parsed_select,
            "exclude_branch": parsed_exclude,
        },
        debug=True,
    )
    _names_versions_to_pre_build = [x.name for x in ver._versions_to_pre_build]
    for tag in select:
        assert tag in _names_versions_to_pre_build
    for tag in exclude:
        assert tag not in _names_versions_to_pre_build
    return


def test_top_level_index():
    assert OUTPATH.exists()
    assert (OUTPATH / "index.html").is_file()
    return


def test_branch_selection():
    # v1.0 and main should exist, v2.0/anyother shouldn't
    versions_should_exist = list(VERSIONS_SUPPOSED.keys())
    # `versions_should_exist` plus top-level index.html
    versions_should_exist.append("index.html")
    # get files and folders in the outpath
    outpath_glob = OUTPATH.glob("*")
    for filefolder in outpath_glob:
        assert filefolder.name in versions_should_exist
    return


@pytest.mark.parametrize("ver, file", [(x, z) for x, y in VERSIONS_SUPPOSED.items() for z in y])
def test_injected_hyperlinks(ver, file):
    assert (OUTPATH / ver / file).is_file()

    data = None
    with open(OUTPATH / ver / file) as f:
        data = f.read()
    soup = bs(data, features="html.parser")
    injected_code = soup.find_all(class_="injected")

    # Injected code must exist
    assert injected_code

    for inj in injected_code:
        # All hyper-links in the injected code
        hyperlinks = inj.find_all("a")
        hyperlinks_text = set(x.text for x in hyperlinks)

        # Makesure all versions exist in hyperlinks
        assert set(VERSIONS_SUPPOSED.keys()) == hyperlinks_text
        print(f"Versions found in soup: {hyperlinks_text}")

        # Test hyperlinks
        for link in hyperlinks:
            url = pathlib.Path(link.attrs.get("href"))
            filepath = (OUTPATH / ver / file).parent / url
            assert filepath.is_file()

    return
