"""
Graph Service — Builds the graph data structure for the entire vault.
"""

from __future__ import annotations

from models import GraphData, GraphNode, GraphEdge
from services.moc import MOCService
from services.notes import NoteService, WIKILINK_PATTERN, _title_to_id, _id_to_title
from services.vault import VaultManager


class GraphService:
    """Builds a graph representing wikilink relationships between all notes."""

    def __init__(self, moc: MOCService, vault_manager: VaultManager) -> None:
        self.moc = moc
        self.vault = vault_manager

    def build_graph(self, filter_id: str | None = None) -> GraphData:
        """Build the graph from all notes in the vault."""
        if not self.vault.get_active_vault():
            return GraphData(nodes=[], edges=[])
            
        # Collect all note IDs from filesystem
        note_ids: set[str] = set()
        notes_dir = self.vault.notes_dir
        if notes_dir.exists():
            for f in notes_dir.glob("*.md"):
                note_ids.add(f.stem)

        # Build nodes for all notes
        nodes: list[GraphNode] = []
        for nid in note_ids:
            nodes.append(GraphNode(
                id=nid,
                title=_id_to_title(nid),
                labels=[],
            ))

        # Build edges based on wikilinks
        edge_set: set[tuple[str, str]] = set()
        edges: list[GraphEdge] = []

        for nid in note_ids:
            path = notes_dir / f"{nid}.md"
            if not path.exists(): continue
            try:
                content = path.read_text(encoding="utf-8")
                for link_title in WIKILINK_PATTERN.findall(content):
                    target_id = _title_to_id(link_title)
                    if target_id in note_ids:
                        key = (nid, target_id)
                        if key not in edge_set:
                            edge_set.add(key)
                            edges.append(GraphEdge(source=nid, target=target_id, type="reference"))
            except Exception:
                continue

        return GraphData(nodes=nodes, edges=edges)
