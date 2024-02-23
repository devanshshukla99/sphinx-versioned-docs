import os
import git
import sys
import pathlib


def prepare_ex_file(path):
    with open(path / "example.rst", "w") as f:
        f.write("Obi-Wan\n")
        f.write("=======\n")
        f.write("Hello there.\n General Kenobi!\n")
        f.flush()

    npath = path / "code_ref" / "api_ref"
    if not npath.exists():
        npath.mkdir(parents=True)

    with open(npath / "example2.rst", "w") as f:
        f.write("Obi-Wan\n")
        f.write("=======\n")
        f.write("Hello there.\n General Kenobi!\n")
        f.flush()
    return True


def add_ex_file_to_index(path):
    data = ""
    with open(path / "index.rst", "r") as f:
        data = f.read()

    if "example.rst" in data:
        return True

    data = data.replace(
        ":caption: Contents:", ":caption: Contents:\n\n   example.rst\n   code_ref/api_ref/example2.rst\n"
    )
    with open(path / "index.rst", "w") as f:
        f.write(data)
    return True


def prepare_repo(path):
    if (path / ".git").exists():
        print("Repo already exists...")
        print("Exiting...")
        exit(-1)

    print("No existing repo; making...")
    repo = git.Repo.init(path)

    repo.git.add(".")
    repo.index.commit("initial")

    repo.git.checkout("-b", "main")
    repo.git.branch("-D", "master")

    print("Success")
    return repo


def main(path):
    path = pathlib.Path(path)
    basepath = path / "docs"

    # Verify `docs` exists
    assert basepath.exists()

    # Prepare git-repo
    repo = prepare_repo(path)

    # Insert `html_theme` in `conf.py` as specified in cli-arg
    with open(basepath / "conf.py", "a") as f:
        f.write(f"html_theme = '{sys.argv[1]}'\n")

    # Commit changes in `conf.py`
    repo.git.add(basepath / "conf.py")
    repo.index.commit("Added `html_theme` in `conf.py`")

    # Tag this version
    repo.create_tag("v1.0")

    # Prepare an example file
    assert prepare_ex_file(basepath)
    assert add_ex_file_to_index(basepath)

    # Commit example files
    repo.git.add(basepath / "example.rst")
    repo.git.add(basepath / "code_ref/api_ref/example2.rst")
    repo.git.add(basepath / "index.rst")
    repo.index.commit("Added `example.rst`")

    # Tag this new version
    repo.create_tag("v2.0")
    return True


if __name__ == "__main__":
    main(os.getcwd())
