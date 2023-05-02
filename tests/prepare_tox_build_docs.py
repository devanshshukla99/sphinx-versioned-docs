import os
from git import Repo


def main(path):
    if not Repo(path).bare:
        pass
    else:
        repo = Repo.init(path)
        repo.git.add(".")
        repo.index.commit("initial")
        repo.git.checkout("-b", "main")
        repo.git.branch("-D", "master")
        print("Success")

    with open(f"{path}/docs/conf.py", "a") as f:
        f.write("html_theme = 'sphinx_rtd_theme'")
    return True


if __name__ == "__main__":
    main(os.getcwd())
