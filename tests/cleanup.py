import os
import shutil
import pathlib


def main(path):
    """
    Method to cleanup `.git` and `docs` directory for setting up testing infrastructure.

    path : `str`
        CWD.
    """
    path = pathlib.Path(path)

    if (path / ".git").exists():
        shutil.rmtree(path / ".git")
        print(f"rmdir: {path / '.git'}")

    if (path / "docs").exists():
        shutil.rmtree(path / "docs")
        print(f"rmdir: {path / 'docs'}")

    return True


if __name__ == "__main__":
    main(os.getcwd())
