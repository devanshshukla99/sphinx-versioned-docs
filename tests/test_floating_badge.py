import os
import pytest
import pathlib
from bs4 import BeautifulSoup as bs

VERSIONS_SUPPOSED = {
    "v1.0": [
        "index.html",
    ],
    "v2.0": ["index.html", "example.html", "code_ref/api_ref/example2.html"],
    "main": ["index.html", "example.html", "code_ref/api_ref/example2.html"],
}

BASEPATH = pathlib.Path(os.getcwd()) / "docs"
OUTPATH = BASEPATH / "_build"


def test_top_level_index():
    assert OUTPATH.exists()
    assert (OUTPATH / "index.html").is_file()
    return


@pytest.mark.parametrize("ver, file", [(x, z) for x, y in VERSIONS_SUPPOSED.items() for z in y])
def test_floating_version_selector_menu(ver, file):
    assert OUTPATH.exists()
    assert (OUTPATH / ver).exists()
    assert (OUTPATH / ver / file).is_file()

    # Verify `badge_only.css` exists
    assert (OUTPATH / ver / "_static/badge_only.css").is_file()

    data = None
    with open(OUTPATH / ver / file) as f:
        data = f.read()
    soup = bs(data, features="html.parser")
    floating_badge = soup.find_all(class_="rst-badge")

    assert floating_badge

    for inj in floating_badge:
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
