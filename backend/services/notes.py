"""
Notes Service — CRUD operations for Markdown note files.
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

    def _note_path(self, note_id: str) -> Path | None:
        if not self.vault.get_active_vault():
            return None
        return self.vault.notes_dir / f"{note_id}.md"

    def list_notes(self, label: str | None = None) -> list[NoteSummary]:
        """List all notes, optionally filtered by label."""
        notes: list[NoteSummary] = []
        if not self.vault.get_active_vault():
            return notes
        
        for f in self.vault.notes_dir.glob("*.md"):
            note_id = f.stem
            labels = self.moc.get_labels_for_note(note_id)
            if label and label not in labels:
                continue
            notes.append(NoteSummary(
                id=note_id,
                title=_id_to_title(note_id),
                labels=labels,
            ))
        notes.sort(key=lambda n: n.title)
        return notes

    def get_note(self, note_id: str) -> NoteResponse | None:
        """Read a single note from disk."""
        path = self._note_path(note_id)
        if not path or not path.exists():
            return None
        content = path.read_text(encoding="utf-8")
        links = self._parse_wikilinks(content)
        attachments = self._parse_attachments(content)
        labels = self.moc.get_labels_for_note(note_id)
        return NoteResponse(
            id=note_id,
            title=_id_to_title(note_id),
            content=content,
            labels=labels,
            links=links,
            attachments=attachments,
        )

    def get_raw(self, note_id: str) -> str | None:
        """Return raw markdown text (for LLM endpoints)."""
        path = self._note_path(note_id)
        if not path or not path.exists():
            return None
        return path.read_text(encoding="utf-8")

    def create_note(self, title: str, content: str = "", labels: list[str] | None = None) -> NoteResponse:
        """Create a new note. Raises ValueError if it already exists."""
        if not self.vault.get_active_vault():
            raise ValueError("No active vault")
            
        note_id = _title_to_id(title)
        path = self._note_path(note_id)
        if path.exists():  # type: ignore
            raise ValueError(f"Note '{title}' already exists")

        # Reject directory traversal / subdirectory attempts
        if "/" in note_id or "\\" in note_id:
            raise ValueError("Subdirectories are forbidden")

        path.write_text(content, encoding="utf-8")  # type: ignore

        # Update Hierarchy
        if labels:
            for label in labels:
                self.moc.add_to_hierarchy(f"note:{note_id}", f"label:{label}")
        else:
            self.moc.add_to_hierarchy(f"note:{note_id}", "label:Unorganized")

        # Parse links and update edges
        links = self._parse_wikilinks(content)
        self.moc.set_edges_for_note(note_id, [_title_to_id(l) for l in links])

        return self.get_note(note_id)  # type: ignore

    def update_note(self, note_id: str, content: str | None = None, labels: list[str] | None = None) -> NoteResponse | None:
        """Update a note's content and/or labels."""
        path = self._note_path(note_id)
        if not path or not path.exists():
            return None

        old_content = path.read_text(encoding="utf-8")
        old_attachments = set(self._parse_attachments(old_content))

        if content is not None:
            path.write_text(content, encoding="utf-8")
            # Re-parse links
            links = self._parse_wikilinks(content)
            self.moc.set_edges_for_note(note_id, [_title_to_id(l) for l in links])

            # Garbage-collect removed attachments
            new_attachments = set(self._parse_attachments(content))
            removed = old_attachments - new_attachments
            for filename in removed:
                self.attachments.decrement_ref(filename)
        
        if labels is not None:
            # Sync with hierarchy
            self.moc.remove_from_hierarchy(f"note:{note_id}")
            for label in labels:
                self.moc.add_to_hierarchy(f"note:{note_id}", f"label:{label}")

        return self.get_note(note_id)

    def delete_note(self, note_id: str) -> bool:
        """Delete a note and clean up all references."""
        path = self._note_path(note_id)
        if not path or not path.exists():
            return False

        # Get attachments before deleting
        content = path.read_text(encoding="utf-8")
        attachments = self._parse_attachments(content)

        # Delete the file
        path.unlink()

        # Remove from Hierarchy
        self.moc.remove_from_hierarchy(f"note:{note_id}")
        self.moc.remove_edges_for_note(note_id)

        # GC attachments
        for filename in attachments:
            self.attachments.decrement_ref(filename)

        return True

    def rename_note(self, old_id: str, new_title: str) -> NoteResponse | None:
        """Rename a note (changes filename and updates all MOC references)."""
        old_path = self._note_path(old_id)
        if not old_path or not old_path.exists():
            return None

        new_id = _title_to_id(new_title)
        new_path = self._note_path(new_id)
        if new_path.exists(): # type: ignore
            raise ValueError(f"Note '{new_title}' already exists")

        # Read content and move file
        content = old_path.read_text(encoding="utf-8")
        new_path.write_text(content, encoding="utf-8") # type: ignore
        old_path.unlink()

        # Preserve labels
        labels = self.moc.get_labels_for_note(old_id)

        # Remove old note from MOC
        self.moc.remove_note_from_all_labels(old_id)
        self.moc.remove_edges_for_note(old_id)

        # Add new note to MOC with same labels
        if labels:
            self.moc.assign_note_to_labels(new_id, labels)

        # Re-parse links
        links = self._parse_wikilinks(content)
        self.moc.set_edges_for_note(new_id, [_title_to_id(l) for l in links])

        return self.get_note(new_id)

    def search_titles(self, query: str) -> list[NoteSummary]:
        """Search note titles for autocomplete."""
        query_lower = query.lower()
        results = []
        if not self.vault.get_active_vault():
            return results
            
        for f in self.vault.notes_dir.glob("*.md"):
            title = _id_to_title(f.stem)
            if query_lower in title.lower():
                results.append(NoteSummary(
                    id=f.stem,
                    title=title,
                    labels=self.moc.get_labels_for_note(f.stem),
                ))
        return results

    # ── Parsing helpers ──────────────────────────────────

    @staticmethod
    def _parse_wikilinks(content: str) -> list[str]:
        """Extract [[Note Title]] links from markdown content."""
        return WIKILINK_PATTERN.findall(content)

    @staticmethod
    def _parse_attachments(content: str) -> list[str]:
        """Extract ![[filename]] attachment references from markdown content."""
        return ATTACHMENT_PATTERN.findall(content)
