from __future__ import annotations

import configparser
import re
import subprocess
from pathlib import Path
from typing import Iterable

import click

GLOBAL_STORE = Path.home() / ".local" / "share" / "git-flash"


def _run(args: Iterable[str], cwd: Path | None = None) -> None:
    subprocess.check_call(list(args), cwd=cwd)


def _parse_repo(repo: str) -> tuple[str, Path]:
    if "://" in repo:
        url = repo
        safe = re.sub(r"[^A-Za-z0-9._-]", "_", repo)
        path = GLOBAL_STORE / "extern" / f"{safe}"
    else:
        owner, name = repo.split("/", 1)
        if name.endswith(".git"):
            name = name[:-4]
        url = f"https://github.com/{owner}/{name}.git"
        path = GLOBAL_STORE / "github" / owner / f"{name}.git"
    return url, path


def _ensure_global_repo(url: str, repo_path: Path) -> None:
    if not repo_path.exists():
        repo_path.parent.mkdir(parents=True, exist_ok=True)
        _run(["git", "clone", "--bare", url, str(repo_path)])
    else:
        _run(["git", "-C", str(repo_path), "fetch", "--all", "--tags", "--force"])


def _worktree_add(repo_path: Path, dest: Path, ref: str) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        return
    _run(["git", "-C", str(repo_path), "worktree", "add", "--detach", str(dest), ref])


def _get_submodules(dest: Path) -> list[tuple[str, str, str]]:
    gitmodules = dest / ".gitmodules"
    if not gitmodules.exists():
        return []
    config = configparser.ConfigParser()
    config.read(gitmodules)
    subs: list[tuple[str, str, str]] = []
    for name in config.sections():
        path = config[name]["path"]
        url = config[name]["url"]
        try:
            commit = subprocess.check_output(
                ["git", "rev-parse", f"HEAD:{path}"], cwd=dest, text=True
            ).strip()
        except subprocess.CalledProcessError:
            continue
        subs.append((path, url, commit))
    return subs


def flash(repo: str, destination: Path, ref: str | None = None) -> None:
    url, repo_path = _parse_repo(repo)
    _ensure_global_repo(url, repo_path)
    _worktree_add(repo_path, destination, ref or "HEAD")
    for path, url, commit in _get_submodules(destination):
        flash(url, destination / path, commit)


@click.command()
@click.argument("repo")
@click.argument("destination")
def main(repo: str, destination: str) -> None:
    """Flash REPO into DESTINATION using git worktrees."""
    dest = Path(destination).expanduser().resolve()
    flash(repo, dest)
