"""
MOC Service — Read/write the graph_moc.yaml file with a fully flexible unified hierarchy.
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
        """Load the MOC from disk and migrate if needed."""
        with self._lock:
            if not self.vault.get_active_vault():
                self._moc = GraphMOC()
                return self._moc
                
            moc_file = self.vault.moc_file
            if moc_file.exists():
                raw = yaml.safe_load(moc_file.read_text(encoding="utf-8")) or {}
                
                # Load edges
                edges = []
                for e in raw.get("edges", []):
                    edges.append(EdgeEntry(
                        **{"from": e.get("from", ""), "to": e.get("to", ""), "type": e.get("type", "reference")}
                    ))
                
                # Load hierarchy
                hierarchy = [HierarchyEntry(**h) for h in raw.get("hierarchy", [])]
                
                # Migration: if hierarchy is empty but labels exist, convert labels
                labels = raw.get("labels", [])
                if not hierarchy and labels:
                    hierarchy = self._migrate_labels(labels)

                self._moc = GraphMOC(
                    version=raw.get("version", 1.1),
                    hierarchy=hierarchy,
                    edges=edges,
                )
                self._sync_with_filesystem()
            else:
                self._moc = GraphMOC()
                self._sync_with_filesystem()
            return self._moc

    def _sync_with_filesystem(self) -> None:
        """Ensure all markdown files have a node in the hierarchy."""
        if not self._moc or not self.vault.get_active_vault():
            return

        notes_dir = self.vault.notes_dir
        if not notes_dir.exists():
            return

        # Get all note IDs from filesystem
        fs_note_ids = {f"note:{f.stem}" for f in notes_dir.glob("*.md")}
        
        # Get all IDs currently in hierarchy (nodes)
        h_node_ids = {n.id for n in self._moc.hierarchy}
        
        # Get all IDs that are children of someone
        all_children = set()
        for n in self._moc.hierarchy:
            for cid in n.children:
                all_children.add(cid)
        
        changed = False

        # 1. Find notes completely missing from hierarchy
        missing = fs_note_ids - h_node_ids
        if missing:
            for nid in missing:
                self._ensure_node(nid)
            changed = True

        # 2. Clean up nodes for notes that no longer exist
        existing_h_note_nodes = [n.id for n in self._moc.hierarchy if n.id.startswith("note:")]
        for nid in existing_h_note_nodes:
            if nid not in fs_note_ids:
                self.remove_from_hierarchy(nid)
                changed = True
        
        if changed:
            self.save()

    def _migrate_labels(self, old_labels: list[dict]) -> list[HierarchyEntry]:
        """Convert old flat/slash labels to the new hierarchy structure."""
        new_hierarchy = []
        map_nodes = {}

        for l in old_labels:
            name = l.get("name", "")
            notes = l.get("notes", [])
            
            parts = name.split("/")
            parent_id = None
            
            for i in range(len(parts)):
                current_path = "/".join(parts[:i+1])
                node_id = f"label:{current_path}"
                
                if node_id not in map_nodes:
                    node = HierarchyEntry(id=node_id, children=[])
                    map_nodes[node_id] = node
                    new_hierarchy.append(node)
                    
                    if parent_id:
                        p_node = map_nodes[parent_id]
                        if node_id not in p_node.children:
                            p_node.children.append(node_id)
                
                parent_id = node_id
            
            # Add notes
            leaf_node = map_nodes[f"label:{name}"]
            for nid in notes:
                note_node_id = f"note:{nid}"
                if note_node_id not in leaf_node.children:
                    leaf_node.children.append(note_node_id)
                if note_node_id not in map_nodes:
                    map_nodes[note_node_id] = HierarchyEntry(id=note_node_id, children=[])
                    new_hierarchy.append(map_nodes[note_node_id])

        return new_hierarchy

    def save(self, moc: GraphMOC | None = None) -> None:
        """Persist the MOC to disk."""
        if moc is not None:
            self._moc = moc
        if self._moc is None:
            self._moc = GraphMOC()
            
        with self._lock:
            data = {
                "version": 1.1,
                "hierarchy": [h.model_dump() for h in self._moc.hierarchy],
                "edges": [
                    {"from": e.from_note, "to": e.to_note, "type": e.type}
                    for e in self._moc.edges
                ],
            }
            self.vault.moc_file.write_text(yaml.dump(data, default_flow_style=False, allow_unicode=True), encoding="utf-8")

    def get(self) -> GraphMOC:
        if self._moc is None:
            return self.load()
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
        """Add a node to the hierarchy under a parent."""
        self._ensure_node(node_id)
        
        if parent_id:
            parent = self._ensure_node(parent_id)
            if node_id not in parent.children:
                parent.children.append(node_id)
        
        self.save()

    def remove_from_hierarchy(self, node_id: str) -> None:
        """Remove a node and all its references from the hierarchy."""
        moc = self.get()
        # 1. Remove as child from any parent
        for node in moc.hierarchy:
            if node_id in node.children:
                node.children.remove(node_id)
        
        # 2. Remove the node entry itself
        self._moc.hierarchy = [n for n in self._moc.hierarchy if n.id != node_id]
        
        self.save()

    def move_node(self, node_id: str, new_parent_id: str | None) -> None:
        """Change or add parent of a node."""
        moc = self.get()
        
        # If moving a LABEL, it's a true move (remove from old parents)
        if node_id.startswith("label:"):
            for node in moc.hierarchy:
                if node_id in node.children:
                    node.children.remove(node_id)
        
        # If new_parent_id is None, it becomes a root
        if new_parent_id:
            parent = self._ensure_node(new_parent_id)
            if node_id not in parent.children:
                parent.children.append(node_id)
        
        self.save()

    def get_labels_for_note(self, note_id: str) -> list[str]:
        """Find direct label parents."""
        moc = self.get()
        nid = f"note:{note_id}"
        labels = []
        for node in moc.hierarchy:
            if node.id.startswith("label:") and nid in node.children:
                labels.append(node.id.replace("label:", "", 1))
        return labels

    def set_edges_for_note(self, note_id: str, targets: list[str]) -> None:
        moc = self.get()
        moc.edges = [e for e in moc.edges if e.from_note != note_id]
        for target in targets:
            moc.edges.append(EdgeEntry(**{"from": note_id, "to": target, "type": "reference"}))
        self.save()

    def remove_edges_for_note(self, note_id: str) -> None:
        moc = self.get()
        moc.edges = [e for e in moc.edges if e.from_note != note_id and e.to_note != note_id]
        self.save()

    def get_raw_yaml(self) -> str:
        if not self.vault.get_active_vault():
            return ""
        if self.vault.moc_file.exists():
            return self.vault.moc_file.read_text(encoding="utf-8")
        return ""
