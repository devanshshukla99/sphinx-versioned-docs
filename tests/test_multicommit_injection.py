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


@pytest.mark.parametrize("ver, files", VERSIONS_SUPPOSED.items())
def test_existence_of_html_files(ver, files):
    assert OUTPATH.exists()
    assert (OUTPATH / ver).exists()
    print(f"exists: {OUTPATH / ver}")
    for file in files:
        assert (OUTPATH / ver / file).is_file()
        print(f"exists: {OUTPATH / ver / file}")
    return


@pytest.mark.parametrize("ver, files", VERSIONS_SUPPOSED.items())
def test_existence_of_files_secondary(ver, files):
    check_files = VERSIONS_SUPPOSED.get("main")

    # Additional/unnecessary check for mental-sanity
    assert (OUTPATH / ver).exists()
    for check in check_files:
        check_expected_result = check in files
        print(f"{ver}|{check}: {(OUTPATH / ver / check).exists()} vs {check_expected_result}")
        assert (OUTPATH / ver / check).exists() is check_expected_result
    return


@pytest.mark.parametrize(
    "ver, expected", ((x, y) for x, y in zip(VERSIONS_SUPPOSED.keys(), [False, True, True]))
)
def test_file_content(ver, expected):
    # Verify content of `example.html`
    file = "example.html"
    content_to_verify = "Hello there.\n General Kenobi!\n"

    # Verify existence of `example.html`
    assert (OUTPATH / ver / file).is_file() is expected

    # If not expected, then
    if not expected:
        return

    # Verify the contents of `example.html`, if expected
    data = None
    with open(OUTPATH / ver / file, encoding="utf8") as f:
        data = f.read()
    for content in content_to_verify.split():
        assert content in data
    print(f"exists: obi-wan: {OUTPATH / ver / file}")
    return


@pytest.mark.parametrize("ver, file", [(x, z) for x, y in VERSIONS_SUPPOSED.items() for z in y])
def test_injected_hyperlinks(ver, file):
    assert (OUTPATH / ver / file).is_file()

    data = None
    with open(OUTPATH / ver / file, encoding="utf8") as f:
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
