"""
MOC Service — Unified hierarchy with strict exclusive membership (one parent per note).
Optimized for clean YAML (removes redundant leaf entries).
"""

from __future__ import annotations

import threading
from pathlib import Path

import yaml

from models import GraphMOC, HierarchyEntry, EdgeEntry
from services.vault import VaultManager


class MOCService:
    """Thread-safe read/write access to the YAML Map of Content."""

    _lock = threading.RLock()

    def __init__(self, vault_manager: VaultManager) -> None:
        self._moc: GraphMOC | None = None
        self.vault = vault_manager

    # ── Load / Save ──────────────────────────────────────

    def load(self) -> GraphMOC:
        """Load the MOC from disk."""
        with self._lock:
            if not self.vault.get_active_vault():
                self._moc = GraphMOC()
                return self._moc
                
            moc_file = self.vault.moc_file
            if moc_file.exists():
                raw = yaml.safe_load(moc_file.read_text(encoding="utf-8")) or {}
                
                edges_raw = raw.get("edges", [])
                edges = [EdgeEntry(**e) for e in edges_raw]
                
                hierarchy_raw = raw.get("hierarchy", [])
                hierarchy = [HierarchyEntry(**h) for h in hierarchy_raw]

                self._moc = GraphMOC(
                    version=raw.get("version", 1.1),
                    hierarchy=hierarchy,
                    edges=edges,
                )
                self._migrate_to_feeds()
                self._sync_with_filesystem()
            else:
                self._moc = GraphMOC()
                self._sync_with_filesystem()
            return self._moc

    def _migrate_to_feeds(self) -> None:
        """Convert root-level 'label:' nodes to 'feed:' for cleaner YAML."""
        if not self._moc: return
        child_ids = set()
        for n in self._moc.hierarchy:
            for cid in n.children:
                child_ids.add(cid)
        changed = False
        for n in self._moc.hierarchy:
            if n.id.startswith("label:") and n.id not in child_ids:
                old_id = n.id
                new_id = old_id.replace("label:", "feed:", 1)
                n.id = new_id
                for edge in self._moc.edges:
                    if edge.from_note == old_id: edge.from_note = new_id
                    if edge.to_note == old_id: edge.to_note = new_id
                changed = True
        if changed: self.save()

    def _sync_with_filesystem(self) -> None:
        """Ensure all filesystem markdown notes are tracked."""
        if not self._moc or not self.vault.get_active_vault(): return
        notes_dir = self.vault.notes_dir
        if not notes_dir.exists(): return

        # ONLY track .md files in the hierarchy. Drawings/Assets are hidden.
        fs_note_ids = {f"note:{f.stem}" for f in notes_dir.glob("*.md")}
        
        # Build map of all IDs currently tracked (either as node or child)
        tracked_ids = set()
        for n in self._moc.hierarchy:
            tracked_ids.add(n.id)
            for cid in n.children:
                tracked_ids.add(cid)
        
        changed = False
        
        # 1. Add notes that are completely missing from the MOC
        missing = fs_note_ids - tracked_ids
        for nid in missing:
            self._ensure_node(nid)
            changed = True

        # 2. Cleanup: If a note is listed as a ROOT node in the hierarchy list 
        # BUT it also exists as a child of another node, prune the redundant root entry.
        child_ids = set()
        for n in self._moc.hierarchy:
            for cid in n.children:
                child_ids.add(cid)

        original_hierarchy = list(self._moc.hierarchy)
        # Filter: Keep if it's not a note, or if it's a note that isn't redundant
        # ALSO: Remove any note entries that don't match a filesystem .md file
        self._moc.hierarchy = [
            n for n in original_hierarchy 
            if not (n.id.startswith("note:") and (n.id in child_ids and not n.children))
        ]
        
        # Prune notes from hierarchy that don't exist as .md on disk
        self._moc.hierarchy = [
            n for n in self._moc.hierarchy
            if not (n.id.startswith("note:") and n.id not in fs_note_ids)
        ]
        
        if len(self._moc.hierarchy) != len(original_hierarchy):
            changed = True
        
        if changed:
            self.save()

    def save(self, moc: GraphMOC | None = None) -> None:
        """Persist to disk with optimization."""
        if moc is not None: self._moc = moc
        if self._moc is None: self._moc = GraphMOC()
            
        with self._lock:
            # Ensure uniqueness
            unique_nodes = {}
            for n in self._moc.hierarchy:
                if n.id not in unique_nodes:
                    unique_nodes[n.id] = n
                else:
                    for cid in n.children:
                        if cid not in unique_nodes[n.id].children:
                            unique_nodes[n.id].children.append(cid)
            
            child_ids = set()
            for n in unique_nodes.values():
                for cid in n.children:
                    child_ids.add(cid)
            
            clean_hierarchy = []
            for node_id, n in unique_nodes.items():
                is_root = node_id not in child_ids
                has_children = len(n.children) > 0
                is_category = node_id.startswith("label:") or node_id.startswith("feed:")
                
                if is_root or has_children or is_category:
                    clean_hierarchy.append(n.model_dump())

            data = {
                "version": 1.1,
                "hierarchy": clean_hierarchy,
                "edges": [{"from": e.from_note, "to": e.to_note, "type": e.type} for e in self._moc.edges],
            }
            self.vault.moc_file.write_text(yaml.dump(data, default_flow_style=False, allow_unicode=True), encoding="utf-8")
            self._moc.hierarchy = [HierarchyEntry(**h) for h in clean_hierarchy]

    def get(self) -> GraphMOC:
        if self._moc is None: return self.load()
        return self._moc

    # ── Hierarchy Operations ──────────────────────────────

    def _ensure_node(self, node_id: str) -> HierarchyEntry:
        moc = self.get()
        node = next((n for n in moc.hierarchy if n.id == node_id), None)
        if not node:
            node = HierarchyEntry(id=node_id, children=[])
            moc.hierarchy.append(node)
        return node

    def add_to_hierarchy(self, node_id: str, parent_id: str | None = None) -> None:
        """Add node to parent with strict single-parent enforcement."""
        self._ensure_node(node_id)
        
        moc = self.get()
        for n in moc.hierarchy:
            if node_id in n.children:
                n.children.remove(node_id)

        if parent_id:
            parent = self._ensure_node(parent_id)
            if node_id not in parent.children:
                parent.children.append(node_id)
        
        self.save()

    def move_node(self, node_id: str, new_parent_id: str | None) -> None:
        self.add_to_hierarchy(node_id, new_parent_id)

    def remove_from_hierarchy(self, node_id: str) -> None:
        moc = self.get()
        for node in moc.hierarchy:
            if node_id in node.children:
                node.children.remove(node_id)
        self._moc.hierarchy = [n for n in self._moc.hierarchy if n.id != node_id]
        self.save()

    def get_labels_for_note(self, note_id: str) -> list[str]:
        moc = self.get()
        nid = f"note:{note_id}"
        labels = []
        for node in moc.hierarchy:
            if (node.id.startswith("label:") or node.id.startswith("feed:")) and nid in node.children:
                labels.append(node.id.split(":", 1)[1])
        return labels

    def get_canvas_note_ids(self, canvas_id: str) -> set[str]:
        moc = self.get()
        canvas_node = next((n for n in moc.hierarchy if n.id == canvas_id), None)
        if not canvas_node: return set()
        return {cid.replace("note:", "", 1) for cid in canvas_node.children if cid.startswith("note:")}

    def get_raw_yaml(self) -> str:
        if not self.vault.get_active_vault(): return ""
        if self.vault.moc_file.exists():
            return self.vault.moc_file.read_text(encoding="utf-8")
        return ""
