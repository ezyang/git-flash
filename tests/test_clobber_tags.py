import asyncio
import subprocess
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))
import git_zap.cli as cli
from git_zap.cli import zap


def _git(args, cwd: Path) -> None:
    subprocess.check_call(["git", *args], cwd=cwd)


def test_tags_are_clobbered(tmp_path: Path) -> None:
    cli.GLOBAL_STORE = tmp_path / "store"

    origin = tmp_path / "origin"
    origin.mkdir()
    _git(["init"], origin)
    (origin / "file.txt").write_text("one")
    _git(["add", "file.txt"], origin)
    _git(["commit", "-m", "one"], origin)
    _git(["tag", "foo"], origin)

    dest1 = tmp_path / "dest1"
    asyncio.run(zap(origin.as_uri(), dest1))

    (origin / "file.txt").write_text("two")
    _git(["add", "file.txt"], origin)
    _git(["commit", "-m", "two"], origin)
    _git(["tag", "-f", "foo"], origin)

    dest2 = tmp_path / "dest2"
    asyncio.run(zap(origin.as_uri(), dest2))

    _, repo_path = cli._parse_repo(origin.as_uri())
    tag_commit = subprocess.check_output(
        ["git", "-C", str(repo_path), "rev-parse", "refs/tags/foo"],
        text=True,
    ).strip()
    head_commit = subprocess.check_output(
        ["git", "-C", str(origin), "rev-parse", "HEAD"],
        text=True,
    ).strip()
    assert tag_commit == head_commit
