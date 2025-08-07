import asyncio
import subprocess
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))
import git_zap.cli as cli  # noqa: E402
from git_zap.cli import zap  # noqa: E402


def _git(args, cwd: Path) -> None:
    subprocess.check_call(["git", *args], cwd=cwd)


def test_empty_submodule_dir_is_replaced(tmp_path: Path) -> None:
    cli.GLOBAL_STORE = tmp_path / "store"

    sub_repo = tmp_path / "sub"
    sub_repo.mkdir()
    _git(["init"], sub_repo)
    (sub_repo / "file.txt").write_text("content")
    _git(["add", "file.txt"], sub_repo)
    _git(["commit", "-m", "init"], sub_repo)

    main_repo = tmp_path / "main"
    main_repo.mkdir()
    _git(["init"], main_repo)
    _git(
        [
            "-c",
            "protocol.file.allow=always",
            "submodule",
            "add",
            sub_repo.as_uri(),
            "sub",
        ],
        main_repo,
    )
    _git(["commit", "-m", "add submodule"], main_repo)

    dest = tmp_path / "checkout"
    asyncio.run(zap(main_repo.as_uri(), dest))

    output = subprocess.check_output(
        ["git", "submodule", "update", "--init", "--recursive"],
        cwd=dest,
        text=True,
    )
    assert output.strip() == ""
