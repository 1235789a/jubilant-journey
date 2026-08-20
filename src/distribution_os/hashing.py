from __future__ import annotations

import hashlib
from pathlib import Path


IGNORED_NAMES = {".DS_Store", "__pycache__"}


def content_hash(path: Path) -> str:
    path = Path(path)
    digest = hashlib.sha256()
    if path.is_file():
        digest.update(path.name.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        return digest.hexdigest()
    if not path.is_dir():
        raise FileNotFoundError(path)
    for item in sorted(candidate for candidate in path.rglob("*") if candidate.is_file()):
        if any(part.startswith(".") or part in IGNORED_NAMES for part in item.parts):
            continue
        digest.update(item.relative_to(path).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(item.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def stable_key(*parts: object) -> str:
    payload = "\x1f".join("" if part is None else str(part) for part in parts)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
