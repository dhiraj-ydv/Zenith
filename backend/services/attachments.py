"""
Attachment Service — File upload, reference counting, and garbage collection.
"""

from __future__ import annotations

import re
import threading
from pathlib import Path

from services.vault import VaultManager


class AttachmentService:
    """Manages attachments with reference counting and auto-delete GC."""

    _lock = threading.Lock()

    def __init__(self, vault_manager: VaultManager) -> None:
        self.vault = vault_manager
        # Lazy-loaded ref counts: filename -> count
        self._ref_counts: dict[str, int] | None = None

    def _build_ref_counts(self) -> dict[str, int]:
        """Scan all notes and count attachment references."""
        pattern = re.compile(r"!\[\[([^\]]+)\]\]")
        counts: dict[str, int] = {}
        
        if not self.vault.get_active_vault():
            return counts

        attachments_dir = self.vault.attachments_dir
        notes_dir = self.vault.notes_dir

        # Initialize with all files in attachments dir
        if attachments_dir.exists():
            for f in attachments_dir.iterdir():
                if f.is_file():
                    counts[f.name] = 0

        # Count references from notes
        if notes_dir.exists():
            for note_file in notes_dir.glob("*.md"):
                content = note_file.read_text(encoding="utf-8")
                for match in pattern.findall(content):
                    if match in counts:
                        counts[match] += 1
                    else:
                        counts[match] = 1

        return counts

    @property
    def ref_counts(self) -> dict[str, int]:
        if self._ref_counts is None:
            self._ref_counts = self._build_ref_counts()
        return self._ref_counts

    def rebuild_counts(self) -> None:
        """Force-rebuild reference counts from disk."""
        with self._lock:
            self._ref_counts = self._build_ref_counts()

    def save_attachment(self, filename: str, data: bytes) -> str:
        """Save an attachment file to disk. Returns the filename."""
        if not self.vault.get_active_vault():
            raise ValueError("No active vault")
            
        # Sanitize filename — no directory traversal
        safe_name = Path(filename).name
        if not safe_name:
            raise ValueError("Invalid filename")

        dest = self.vault.attachments_dir / safe_name

        # Handle duplicate filenames
        counter = 1
        stem = dest.stem
        suffix = dest.suffix
        while dest.exists():
            dest = self.vault.attachments_dir / f"{stem}_{counter}{suffix}"
            safe_name = dest.name
            counter += 1

        dest.write_bytes(data)

        with self._lock:
            self.ref_counts[safe_name] = 0

        return safe_name

    def get_attachment_path(self, filename: str) -> Path | None:
        """Return the path to an attachment, or None if it doesn't exist."""
        if not self.vault.get_active_vault():
            return None
        path = self.vault.attachments_dir / filename
        if path.exists() and path.is_file():
            return path
        return None

    def list_attachments(self) -> list[dict]:
        """List all attachments with their reference counts."""
        result = []
        if not self.vault.get_active_vault():
            return result
            
        attachments_dir = self.vault.attachments_dir
        if attachments_dir.exists():
            for f in attachments_dir.iterdir():
                if f.is_file():
                    result.append({
                        "filename": f.name,
                        "size": f.stat().st_size,
                        "ref_count": self.ref_counts.get(f.name, 0),
                    })
        return result

    def increment_ref(self, filename: str) -> None:
        """Increment reference count for an attachment."""
        with self._lock:
            self.ref_counts[filename] = self.ref_counts.get(filename, 0) + 1

    def decrement_ref(self, filename: str) -> None:
        """Decrement reference count and garbage-collect if zero."""
        with self._lock:
            current = self.ref_counts.get(filename, 0)
            new_count = max(0, current - 1)
            self.ref_counts[filename] = new_count

            if new_count == 0:
                self._gc_file(filename)

    def _gc_file(self, filename: str) -> None:
        """Delete an attachment file if it has zero references."""
        if not self.vault.get_active_vault():
            return
        path = self.vault.attachments_dir / filename
        if path.exists():
            path.unlink()
            self.ref_counts.pop(filename, None)
            print(f"[GC] Deleted orphaned attachment '{filename}'")

    def run_full_gc(self) -> list[str]:
        """Run a full garbage collection pass. Returns list of deleted files."""
        if not self.vault.get_active_vault():
            return []
            
        self.rebuild_counts()
        deleted = []
        with self._lock:
            for filename, count in list(self.ref_counts.items()):
                if count == 0:
                    path = self.vault.attachments_dir / filename
                    if path.exists():
                        path.unlink()
                        deleted.append(filename)
                        self.ref_counts.pop(filename, None)
        return deleted
