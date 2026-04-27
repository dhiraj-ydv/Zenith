"""
Vault Service — Manages multiple vaults and global settings.
"""

import json
import os
from pathlib import Path

from models import VaultSettings

# Global settings path
SETTINGS_DIR = Path.home() / ".zenith"
SETTINGS_FILE = SETTINGS_DIR / "settings.json"


class VaultManager:
    """Manages global settings and the currently active vault."""

    def __init__(self):
        self.settings: VaultSettings = self._load_settings()

    def _load_settings(self) -> VaultSettings:
        if SETTINGS_FILE.exists():
            try:
                data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
                return VaultSettings(**data)
            except Exception:
                pass
        return VaultSettings()

    def _save_settings(self):
        SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
        SETTINGS_FILE.write_text(self.settings.model_dump_json(indent=2), encoding="utf-8")

    def get_active_vault(self) -> str | None:
        return self.settings.active_vault

    def set_active_vault(self, path: str):
        path_obj = Path(path).resolve()
        path_str = str(path_obj)
        if path_str not in self.settings.vaults:
            self.settings.vaults.append(path_str)
        self.settings.active_vault = path_str
        self._save_settings()
        self.init_vault(path_str)

    def add_vault(self, path: str):
        path_obj = Path(path).resolve()
        path_str = str(path_obj)
        if path_str not in self.settings.vaults:
            self.settings.vaults.append(path_str)
            self._save_settings()

    def remove_vault(self, path: str):
        path_obj = Path(path).resolve()
        path_str = str(path_obj)
        if path_str in self.settings.vaults:
            self.settings.vaults.remove(path_str)
            if self.settings.active_vault == path_str:
                self.settings.active_vault = self.settings.vaults[0] if self.settings.vaults else None
            self._save_settings()

    def get_vaults(self) -> list[str]:
        return self.settings.vaults

    # Path helpers for the active vault
    def _ensure_active(self):
        if not self.settings.active_vault:
            raise ValueError("No active vault selected")

    @property
    def vault_root(self) -> Path:
        self._ensure_active()
        return Path(self.settings.active_vault)  # type: ignore

    @property
    def notes_dir(self) -> Path:
        return self.vault_root / "notes"

    @property
    def attachments_dir(self) -> Path:
        return self.vault_root / "attachments"

    @property
    def uploads_dir(self) -> Path:
        return self.attachments_dir / "Uploads"

    @property
    def excalidraw_dir(self) -> Path:
        return self.attachments_dir / "Excalidraw"

    @property
    def moc_file(self) -> Path:
        return self.vault_root / "graph_moc.yaml"

    def init_vault(self, path_str: str | None = None) -> None:
        """Create the vault directory structure if it doesn't exist."""
        if path_str is None:
            if not self.settings.active_vault:
                return
            root = self.vault_root
        else:
            root = Path(path_str)

        notes = root / "notes"
        attachments = root / "attachments"
        uploads = attachments / "Uploads"
        excalidraw = attachments / "Excalidraw"
        moc = root / "graph_moc.yaml"

        notes.mkdir(parents=True, exist_ok=True)
        attachments.mkdir(parents=True, exist_ok=True)
        uploads.mkdir(parents=True, exist_ok=True)
        excalidraw.mkdir(parents=True, exist_ok=True)

        if not moc.exists():
            moc.write_text("version: 1.1\nhierarchy: []\nedges: []\n", encoding="utf-8")

        print(f"[OK] Vault ready at {root}")

    def validate_flat_structure(self) -> list[str]:
        """Validate that no subdirectories exist inside /notes. Subdirectories in /attachments are allowed."""
        violations: list[str] = []
        if not self.settings.active_vault:
            return violations
        
        # Only check notes_dir for flat structure now
        if self.notes_dir.exists():
            for child in self.notes_dir.iterdir():
                if child.is_dir():
                    violations.append(str(child))
        return violations
