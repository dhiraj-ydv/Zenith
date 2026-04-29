"""
MOC Service — Unified hierarchy with cycle-safe parent/child relationships.
Optimized for clean YAML while preserving nested note/label structures.
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
        """Ensure all filesystem notes (md, lorien, xopp) are tracked."""
        if not self._moc or not self.vault.get_active_vault(): return
        
        # Track .md, .lorien, and .xopp files in the hierarchy.
        fs_note_ids = {f"note:{f.stem}" for f in self.vault.notes_dir.glob("*.md")}
        if self.vault.lorien_notes_dir.exists():
            fs_note_ids.update({f"note:{f.stem}" for f in self.vault.lorien_notes_dir.glob("*.lorien")})
        if self.vault.xjournal_dir.exists():
            fs_note_ids.update({f"note:{f.stem}" for f in self.vault.xjournal_dir.glob("*.xopp")})
        
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

        # 3. Hierarchy Doctor: Detect and break floating cycles
        # A floating cycle happens when nodes point to each other but no root points to them.
        all_ids = {n.id for n in self._moc.hierarchy}
        child_to_parents: dict[str, list[str]] = {}
        for n in self._moc.hierarchy:
            for cid in n.children:
                child_to_parents.setdefault(cid, []).append(n.id)
        
        # Roots are nodes with no parents
        roots = {nid for nid in all_ids if nid not in child_to_parents}
        
        reachable = set()
        def mark_reachable(nid):
            if nid in reachable: return
            reachable.add(nid)
            node = next((n for n in self._moc.hierarchy if n.id == nid), None)
            if node:
                for cid in node.children: mark_reachable(cid)
        
        for root_id in roots:
            mark_reachable(root_id)
            
        # Floating nodes are IDs in hierarchy that are not reachable
        floating = all_ids - reachable
        if floating:
            # Break cycles by removing floating nodes from their parents' children list
            for fid in floating:
                for n in self._moc.hierarchy:
                    if fid in n.children:
                        n.children.remove(fid)
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

    def _is_descendant(self, potential_descendant_id: str, ancestor_id: str, path: set[str] | None = None) -> bool:
        """Check if a node is already a descendant of another node (cycle detection)."""
        if path is None: path = set()
        if potential_descendant_id == ancestor_id: return True
        if ancestor_id in path: return False # Cycle already present elsewhere
        
        path.add(ancestor_id)
        moc = self.get()
        node = next((n for n in moc.hierarchy if n.id == ancestor_id), None)
        if not node: return False
        
        for child_id in node.children:
            if self._is_descendant(potential_descendant_id, child_id, path.copy()):
                return True
        return False

    def _remove_from_parents(self, node_id: str, *, category_only: bool = False) -> None:
        """Detach a node from its parents, optionally only from feed/label parents."""
        moc = self.get()
        for node in moc.hierarchy:
            if category_only and not (node.id.startswith("label:") or node.id.startswith("feed:")):
                continue
            while node_id in node.children:
                node.children.remove(node_id)

    def get_parent_ids(self, node_id: str) -> list[str]:
        """Return all direct parent IDs for a node."""
        parents: list[str] = []
        for node in self.get().hierarchy:
            if node_id in node.children:
                parents.append(node.id)
        return parents

    def _child_ids(self) -> set[str]:
        child_ids: set[str] = set()
        for node in self.get().hierarchy:
            for child_id in node.children:
                child_ids.add(child_id)
        return child_ids

    def add_to_hierarchy(self, node_id: str, parent_id: str | None = None, *, exclusive: bool = False) -> None:
        """Attach a node to a parent, or reparent exclusively when requested."""
        if parent_id and self._is_descendant(parent_id, node_id):
            # Refuse move that would create a cycle
            return

        self._ensure_node(node_id)

        if exclusive:
            self._remove_from_parents(node_id)

        if parent_id:
            parent = self._ensure_node(parent_id)
            if node_id not in parent.children:
                parent.children.append(node_id)
        
        self.save()

    def move_node(self, node_id: str, new_parent_id: str | None) -> None:
        self.add_to_hierarchy(node_id, new_parent_id, exclusive=True)

    def reorder_node(self, node_id: str, parent_id: str | None, index: int) -> None:
        """Reorder a node among its siblings, including root-level nodes."""
        moc = self.get()
        bounded_index = max(0, index)

        if parent_id:
            parent = next((n for n in moc.hierarchy if n.id == parent_id), None)
            if not parent or node_id not in parent.children:
                return

            siblings = list(parent.children)
            siblings.remove(node_id)
            bounded_index = min(bounded_index, len(siblings))
            siblings.insert(bounded_index, node_id)
            parent.children = siblings
            self.save()
            return

        child_ids = self._child_ids()
        root_entries = [node for node in moc.hierarchy if node.id not in child_ids]
        root_ids = [node.id for node in root_entries]
        if node_id not in root_ids:
            return

        root_ids.remove(node_id)
        bounded_index = min(bounded_index, len(root_ids))
        root_ids.insert(bounded_index, node_id)

        root_map = {node.id: node for node in root_entries}
        non_roots = [node for node in moc.hierarchy if node.id in child_ids]
        moc.hierarchy = [root_map[rid] for rid in root_ids] + non_roots
        self.save()

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
