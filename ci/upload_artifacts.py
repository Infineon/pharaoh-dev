"""
This script is supposed to be executed as pre-command in a tox environment,
which uploads the final package to Artifactory.
It searches the dist directory for tar.gz and whl files and check that no artifact with this version already exists on
Artifactory, to ensure already released packages are not overwritten (since Artifactory does not prevent the admin,
who is uploading, from overwriting the artifact).
If any artifact already exist the script will throw an exception and the tox env will abort and not upload anything.
"""

import json
import re
import shlex
import subprocess as sp
import urllib.request
from pathlib import Path

REPO = "pypi-des-pyverify-local"


def upload_artifacts():
    pkgs = list((Path(__file__).parents[1] / "dist").glob("*.whl")) + list(
        (Path(__file__).parents[1] / "dist").glob("*.tar.gz")
    )

    skip = False
    for pkg in pkgs:
        pkgname = re.findall(r"(.*-[0-9]+\.[0-9]+\.[0-9]+)", pkg.name)
        if len(pkgname) != 1:
            msg = f"Unsupported name/version format in package name {pkg.name}!"
            raise Exception(msg)
        pkgname = pkgname[0]
        results = json.loads(
            urllib.request.urlopen(
                f"https://artifactory.intra.infineon.com/artifactory/api/search/artifact?name={pkgname}"
                f"&repos={REPO}"
            )
            .read()
            .decode()
        ).get("results", [])

        if len(results):
            skip = True
            print(f"Package release {pkgname} already exists on Artifactory! Skipping upload!")

    if skip:
        return

    cmdline = (
        "twine upload "
        f"--repository-url https://artifactory.intra.infineon.com/artifactory/api/pypi/{REPO} "
        "--disable-progress-bar "
        "--verbose "
        "dist/*.whl "
        "dist/*.tar.gz"
    )
    sp.check_call(shlex.split(cmdline))


if __name__ == "__main__":
    upload_artifacts()
