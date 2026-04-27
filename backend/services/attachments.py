"""
Attachment Service — File upload and reference counting.
"""

from __future__ import annotations

import re
import threading
from pathlib import Path

from services.vault import VaultManager


class AttachmentService:
    """Manages attachments with reference counting. Target: /attachments/Uploads"""

    _lock = threading.Lock()

    def __init__(self, vault_manager: VaultManager) -> None:
        self.vault = vault_manager
        self._ref_counts: dict[str, int] | None = None

    def _build_ref_counts(self) -> dict[str, int]:
        """Scan all notes and count attachment references in /attachments/Uploads"""
        pattern = re.compile(r"!\[\[([^\]]+)\]\]")
        counts: dict[str, int] = {}
        
        if not self.vault.get_active_vault():
            return counts

        uploads_dir = self.vault.uploads_dir
        notes_dir = self.vault.notes_dir

        if uploads_dir.exists():
            for f in uploads_dir.iterdir():
                if f.is_file():
                    counts[f.name] = 0

        if notes_dir.exists():
            for note_file in notes_dir.glob("*.md"):
                try:
                    content = note_file.read_text(encoding="utf-8")
                    for match in pattern.findall(content):
                        if match in counts:
                            counts[match] += 1
                        else:
                            counts[match] = 1
                except Exception:
                    continue

        return counts

    @property
    def ref_counts(self) -> dict[str, int]:
        if self._ref_counts is None:
            self._ref_counts = self._build_ref_counts()
        return self._ref_counts

    def rebuild_counts(self) -> None:
        with self._lock:
            self._ref_counts = self._build_ref_counts()

    def save_attachment(self, filename: str, data: bytes) -> str:
        if not self.vault.get_active_vault():
            raise ValueError("No active vault")
            
        safe_name = Path(filename).name
        dest = self.vault.uploads_dir / safe_name

        counter = 1
        stem = dest.stem
        suffix = dest.suffix
        while dest.exists():
            dest = self.vault.uploads_dir / f"{stem}_{counter}{suffix}"
            safe_name = dest.name
            counter += 1

        dest.write_bytes(data)

        with self._lock:
            if self._ref_counts is not None:
                self._ref_counts[safe_name] = 0

        return safe_name

    def get_attachment_path(self, filename: str) -> Path | None:
        if not self.vault.get_active_vault():
            return None
        path = self.vault.uploads_dir / filename
        if path.exists() and path.is_file():
            return path
        return None

    def list_attachments(self) -> list[dict]:
        result = []
        if not self.vault.get_active_vault():
            return result
            
        uploads_dir = self.vault.uploads_dir
        if uploads_dir.exists():
            for f in uploads_dir.iterdir():
                if f.is_file():
                    result.append({
                        "filename": f.name,
                        "size": f.stat().st_size,
                        "ref_count": self.ref_counts.get(f.name, 0),
                    })
        return result

    def increment_ref(self, filename: str) -> None:
        with self._lock:
            self.ref_counts[filename] = self.ref_counts.get(filename, 0) + 1

    def decrement_ref(self, filename: str) -> None:
        with self._lock:
            current = self.ref_counts.get(filename, 0)
            self.ref_counts[filename] = max(0, current - 1)

    def run_full_gc(self) -> list[str]:
        return []
