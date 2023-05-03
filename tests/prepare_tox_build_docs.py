import os
import git
import sys


def main(path):
    try:
        repo = git.Repo(path)
        print("Found existing repo...")
    except git.InvalidGitRepositoryError:
        print("No existing repo; making...")
        repo = git.Repo.init(path)
        repo.git.add(".")
        repo.index.commit("initial")
        repo.git.checkout("-b", "main")
        repo.git.branch("-D", "master")
        print("Success")

    with open(f"{path}/docs/conf.py", "a") as f:
        f.write(f"html_theme = '{sys.argv[1]}'\n")
    return True


if __name__ == "__main__":
    main(os.getcwd())
