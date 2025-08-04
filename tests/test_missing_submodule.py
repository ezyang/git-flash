import subprocess
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))
import git_flash.cli as cli
from git_flash.cli import flash


def _git(args, cwd: Path) -> None:
    subprocess.check_call(["git", *args], cwd=cwd)


def test_missing_submodule_is_ignored(tmp_path: Path) -> None:
    # Use temporary global store to avoid polluting real HOME
    cli.GLOBAL_STORE = tmp_path / "store"

    # Create submodule repository
    sub_repo = tmp_path / "sub"
    sub_repo.mkdir()
    _git(["init"], sub_repo)
    (sub_repo / "file.txt").write_text("content")
    _git(["add", "file.txt"], sub_repo)
    _git(["commit", "-m", "init"], sub_repo)

    # Create main repository with stale .gitmodules entry
    main_repo = tmp_path / "main"
    main_repo.mkdir()
    _git(["init"], main_repo)
    (main_repo / ".gitmodules").write_text(
        f'[submodule "missing"]\n\tpath = third-party/googletest\n\turl = {sub_repo.as_uri()}\n'
    )
    _git(["add", ".gitmodules"], main_repo)
    _git(["commit", "-m", "add submodule"], main_repo)

    dest = tmp_path / "checkout"
    flash(main_repo.as_uri(), dest)
    assert dest.exists()
