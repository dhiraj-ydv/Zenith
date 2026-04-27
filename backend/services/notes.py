"""
Notes Service — CRUD operations for Markdown and Excalidraw files.
"""

from __future__ import annotations

import re
from pathlib import Path

from models import NoteResponse, NoteSummary
from services.moc import MOCService
from services.attachments import AttachmentService
from services.vault import VaultManager


# Regex patterns for parsing
WIKILINK_PATTERN = re.compile(r"\[\[([^\]]+)\]\]")
ATTACHMENT_PATTERN = re.compile(r"!\[\[([^\]]+)\]\]")


def _title_to_id(title: str) -> str:
    """Convert a human title to a filesystem-safe note ID."""
    safe = re.sub(r"[^\w\s\-]", "", title).strip()
    safe = re.sub(r"\s+", "_", safe)
    return safe.lower()


def _id_to_title(note_id: str) -> str:
    """Convert a note ID back to a human-readable title."""
    return note_id.replace("_", " ").title()


class NoteService:
    """Service for managing note lifecycle and link parsing."""

    def __init__(self, moc: MOCService, attachments: AttachmentService, vault_manager: VaultManager) -> None:
        self.moc = moc
        self.attachments = attachments
        self.vault = vault_manager

    def _note_path(self, note_id: str, note_type: str = "markdown") -> Path | None:
        if not self.vault.get_active_vault():
            return None
        if note_type == "excalidraw":
            return self.vault.excalidraw_dir / f"{note_id}.excalidraw"
        return self.vault.notes_dir / f"{note_id}.md"

    def _find_note_file(self, note_id: str) -> tuple[Path, str] | tuple[None, None]:
        """Find either .md in notes/ or .excalidraw in attachments/Excalidraw/."""
        if not self.vault.get_active_vault():
            return None, None
        
        md_path = self.vault.notes_dir / f"{note_id}.md"
        if md_path.exists():
            return md_path, "markdown"
            
        ex_path = self.vault.excalidraw_dir / f"{note_id}.excalidraw"
        if ex_path.exists():
            return ex_path, "excalidraw"
            
        return None, None

    def list_notes(self, label: str | None = None) -> list[NoteSummary]:
        """List only standard markdown notes. Drawings are hidden from sidebar."""
        notes: list[NoteSummary] = []
        if not self.vault.get_active_vault():
            return notes
        
        if self.vault.notes_dir.exists():
            for f in self.vault.notes_dir.glob("*.md"):
                note_id = f.stem
                labels = self.moc.get_labels_for_note(note_id)
                if label and label not in labels:
                    continue
                notes.append(NoteSummary(
                    id=note_id,
                    title=_id_to_title(note_id),
                    labels=labels,
                    type="markdown"
                ))
        notes.sort(key=lambda n: n.title)
        return notes

    def get_note(self, note_id: str) -> NoteResponse | None:
        """Read a note or drawing."""
        path, note_type = self._find_note_file(note_id)
        if not path or not note_type:
            return None
            
        content = path.read_text(encoding="utf-8")
        links = self._parse_wikilinks(content) if note_type == "markdown" else []
        attachments = self._parse_attachments(content) if note_type == "markdown" else []
        labels = self.moc.get_labels_for_note(note_id)
        
        return NoteResponse(
            id=note_id,
            title=_id_to_title(note_id),
            content=content,
            labels=labels,
            links=links,
            attachments=attachments,
            type=note_type
        )

    def create_note(self, title: str, content: str = "", labels: list[str] | None = None, note_type: str = "markdown") -> NoteResponse:
        """Create a new note or drawing."""
        if not self.vault.get_active_vault():
            raise ValueError("No active vault")
            
        note_id = _title_to_id(title)
        existing_path, _ = self._find_note_file(note_id)
        if existing_path:
            raise ValueError(f"'{title}' already exists")

        path = self._note_path(note_id, note_type)
        if not path:
             raise ValueError("Could not determine path")

        path.write_text(content, encoding="utf-8")

        # Only add markdown notes to the virtual hierarchy/sidebar
        if note_type == "markdown":
            if labels:
                for label in labels:
                    full_id = label
                    if not (full_id.startswith("label:") or full_id.startswith("feed:")):
                        full_id = f"label:{label}"
                    self.moc.add_to_hierarchy(f"note:{note_id}", full_id)
            else:
                self.moc.add_to_hierarchy(f"note:{note_id}")

        return self.get_note(note_id)  # type: ignore

    def update_note(self, note_id: str, content: str | None = None, labels: list[str] | None = None) -> NoteResponse | None:
        path, note_type = self._find_note_file(note_id)
        if not path or not note_type:
            return None

        if content is not None:
            path.write_text(content, encoding="utf-8")
        
        if labels is not None and note_type == "markdown":
            self.moc.remove_from_hierarchy(f"note:{note_id}")
            for label in labels:
                full_id = label
                if not (full_id.startswith("label:") or full_id.startswith("feed:")):
                    full_id = f"label:{label}"
                self.moc.add_to_hierarchy(f"note:{note_id}", full_id)

        return self.get_note(note_id)

    def delete_note(self, note_id: str) -> bool:
        path, _ = self._find_note_file(note_id)
        if not path:
            return False

        path.unlink()
        self.moc.remove_from_hierarchy(f"note:{note_id}")
        return True

    def rename_note(self, old_id: str, new_title: str) -> NoteResponse | None:
        old_path, note_type = self._find_note_file(old_id)
        if not old_path or not note_type:
            return None

        new_id = _title_to_id(new_title)
        collision, _ = self._find_note_file(new_id)
        if collision:
            raise ValueError(f"'{new_title}' already exists")

        new_path = self._note_path(new_id, note_type)
        content = old_path.read_text(encoding="utf-8")
        new_path.write_text(content, encoding="utf-8") # type: ignore
        old_path.unlink()

        if note_type == "markdown":
            moc = self.moc.get()
            old_nid = f"note:{old_id}"
            parents = [n.id for n in moc.hierarchy if old_nid in n.children]
            self.moc.remove_from_hierarchy(f"note:{old_id}")
            for p_id in parents:
                self.moc.add_to_hierarchy(f"note:{new_id}", p_id)

        return self.get_note(new_id)

    def get_preview(self, note_id: str) -> bytes | None:
        """Get PNG preview of an Excalidraw drawing if available."""
        # Future-proofing: We could use excalidraw-utils or similar to render to PNG server-side
        # For now, we'll return None or a placeholder if the frontend is expected to handle it
        # However, the user wants it to show in view.
        return None

    def search_titles(self, query: str) -> list[NoteSummary]:
        """Search across all files (including hidden drawings) to allow embedding/linking."""
        query_lower = query.lower()
        results = []
        if not self.vault.get_active_vault():
            return results
            
        # Search notes
        for f in self.vault.notes_dir.glob("*.md"):
            if query_lower in f.stem.lower():
                results.append(NoteSummary(
                    id=f.stem,
                    title=_id_to_title(f.stem),
                    labels=self.moc.get_labels_for_note(f.stem),
                    type="markdown"
                ))
        
        # Search drawings
        for f in self.vault.excalidraw_dir.glob("*.excalidraw"):
            if query_lower in f.stem.lower():
                results.append(NoteSummary(
                    id=f.stem,
                    title=_id_to_title(f.stem),
                    labels=[],
                    type="excalidraw"
                ))
        return results

    @staticmethod
    def _parse_wikilinks(content: str) -> list[str]:
        return WIKILINK_PATTERN.findall(content)

    @staticmethod
    def _parse_attachments(content: str) -> list[str]:
        return ATTACHMENT_PATTERN.findall(content)
