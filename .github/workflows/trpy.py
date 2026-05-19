from os import environ
from pathlib import Path


py = environ["TR_PY_VER"]
py = "".join(py.split(".")[:2])  # Combine major/minor, toss rest
py = py.replace("pypy-", "py")  # For Pypy: have a little less py

tw = environ["TR_TW_VER"]
tw = tw.replace(".", "")

env = (
    f"{environ['TR_TOX_PREFIX']}-py{py}"  # prefix
    f"-tw{tw}{environ['TR_TOX_SUFFIX']}"  # suffix
)

print(f"TOX_ENV={env}")

with Path(environ["GITHUB_ENV"]).open(mode="a") as f:
    f.write(f"TOX_ENV={env}\n")
