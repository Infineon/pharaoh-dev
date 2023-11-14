"""Handles creating a release PR."""
from __future__ import annotations

from pathlib import Path

from git import Commit, Head, Remote, Repo, TagReference
from packaging.version import Version

ROOT_SRC_DIR = Path(__file__).parents[1]


def main(version_str: str) -> None:
    version = Version(version_str)
    repo = Repo(str(ROOT_SRC_DIR))

    if repo.is_dirty():
        msg = "Current repository is dirty. Please commit any changes and try again."
        raise RuntimeError(msg)
    upstream, release_branch = create_release_branch(repo, version)
    try:
        tag = tag_release_commit(repo.head.commit, repo, version)
        print("push release commit")
        repo.git.push(upstream.name, f"{release_branch}:master", "-f")
        print("push release tag")
        repo.git.push(upstream.name, tag, "-f")
    finally:
        print("checkout main to new release and delete release branch")
        repo.heads.master.checkout()
        repo.delete_head(release_branch, force=True)
        upstream.fetch()
        repo.git.reset("--hard", "origin/master")
    print("All done! ✨ 🍰 ✨")


def create_release_branch(repo: Repo, version: Version) -> tuple[Remote, Head]:
    print("create release branch from upstream master")
    upstream = get_upstream(repo)
    upstream.fetch()
    branch_name = f"release-{version}"
    release_branch = repo.create_head(branch_name, upstream.refs.master, force=True)
    upstream.push(refspec=f"{branch_name}:{branch_name}", force=True)
    release_branch.set_tracking_branch(repo.refs[f"{upstream.name}/{branch_name}"])
    release_branch.checkout()
    return upstream, release_branch


def get_upstream(repo: Repo) -> Remote:
    # DEV_REPO = "Infineon/pharaoh-dev.git"
    DEV_REPO = "pyveco/pharaoh-report.git"
    for remote in repo.remotes:
        if any(url.endswith(DEV_REPO) for url in remote.urls):
            return remote
    msg = f"could not find {DEV_REPO} remote"
    raise RuntimeError(msg)


def tag_release_commit(release_commit: Commit, repo: Repo, version: Version) -> TagReference:
    print("tag release commit")
    existing_tags = [x.name for x in repo.tags]
    if version in existing_tags:
        print(f"delete existing tag {version}")
        repo.delete_tag(version)
    print(f"create tag {version}")
    return repo.create_tag(version, ref=release_commit, message=f"release {version}", force=True)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(prog="release")
    parser.add_argument("--version", required=True)
    options = parser.parse_args()
    main(options.version)
