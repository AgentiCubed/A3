"""Local-filesystem ArtifactStore (implements the ArtifactStore port).

Content is addressed by SHA-256 so identical bytes dedupe naturally. An S3/object
adapter would implement the same port without touching callers (architecture §7).
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from app.orchestration.ports import StoredArtifact


class LocalArtifactStore:
    """Stores artifact bytes under ``base_path`` keyed by a relative storage key."""

    def __init__(self, base_path: str) -> None:
        self._base = Path(base_path)
        self._base.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        # Prevent path traversal; keys are simple relative names.
        safe = key.replace("..", "_").lstrip("/")
        return self._base / safe

    def put(self, key: str, data: bytes, content_type: str) -> StoredArtifact:  # noqa: ARG002
        sha = hashlib.sha256(data).hexdigest()
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return StoredArtifact(storage_key=key, size_bytes=len(data), sha256=sha)

    def get(self, key: str) -> bytes:
        return self._path(key).read_bytes()

    def exists(self, key: str) -> bool:
        return self._path(key).exists()
