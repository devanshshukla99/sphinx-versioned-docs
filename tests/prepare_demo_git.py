import os
from git import Repo

def main(path):
    repo = Repo.init(path)
    repo.git.add(".")
    repo.index.commit("initial")
    repo.git.checkout("-b", "main")
    repo.git.branch("-D", "master")
    print("Success")

if __name__=="__main__":
    main(os.getcwd())
