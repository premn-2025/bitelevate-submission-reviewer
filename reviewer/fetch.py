"""Get a submission onto disk safely: local folder, zip file, or public GitHub URL.

Submitted code is only ever read, never executed or installed.
"""
from __future__ import annotations

import re
import subprocess
import tempfile
import zipfile
from pathlib import Path

GITHUB_RE = re.compile(r"^https://github\.com/[A-Za-z0-9_.\-]+/[A-Za-z0-9_.\-]+?(\.git)?/?$")
MAX_ZIP_BYTES = 50_000_000
MAX_ZIP_FILES = 5000


class FetchError(Exception):
    pass


def _safe_extract(zip_path: Path, dest: Path) -> None:
    with zipfile.ZipFile(zip_path) as zf:
        infos = zf.infolist()
        if len(infos) > MAX_ZIP_FILES:
            raise FetchError("Zip has too many files")
        if sum(i.file_size for i in infos) > MAX_ZIP_BYTES:
            raise FetchError("Zip is too large when extracted")
        dest = dest.resolve()
        for info in infos:
            target = (dest / info.filename).resolve()
            if dest not in target.parents and target != dest:
                raise FetchError("Zip contains an unsafe path")
        zf.extractall(dest)


def _single_child(dest: Path) -> Path:
    """If a zip/clone wraps everything in one folder, descend into it."""
    kids = [p for p in dest.iterdir() if p.name != "__MACOSX"]
    if len(kids) == 1 and kids[0].is_dir() and kids[0].name != ".git":
        return kids[0]
    return dest


def prepare(source: str, workdir: str | Path | None = None) -> Path:
    """Return a folder path for `source`. Remote sources go in a temp folder."""
    src = source.strip()
    if GITHUB_RE.match(src):
        dest = Path(workdir or tempfile.mkdtemp(prefix="cynbit_clone_"))
        try:
            subprocess.run(
                ["git", "clone", "--depth", "100", "--single-branch", "--", src, str(dest / "repo")],
                check=True, capture_output=True, text=True, timeout=90,
            )
        except subprocess.CalledProcessError as exc:
            raise FetchError(f"Clone failed: {exc.stderr.strip()[:200]}") from exc
        except subprocess.TimeoutExpired as exc:
            raise FetchError("Clone timed out") from exc
        return dest / "repo"
    path = Path(src).expanduser()
    if path.is_dir():
        return path
    if path.is_file() and path.suffix.lower() == ".zip":
        dest = Path(workdir or tempfile.mkdtemp(prefix="cynbit_zip_"))
        _safe_extract(path, dest)
        return _single_child(dest)
    raise FetchError("Source must be a folder, a .zip file, or a public https://github.com/owner/repo URL")
