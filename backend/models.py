"""
Zenith Pydantic Models — API request/response schemas and YAML MOC structure.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


# ──────────────────────────────────────────────
#  YAML MOC structures
# ──────────────────────────────────────────────

class LabelEntry(BaseModel):
    """A virtual folder / label in the MOC."""
    name: str
    notes: list[str] = Field(default_factory=list)


class EdgeEntry(BaseModel):
    """An explicit edge between two notes."""
    from_note: str = Field(alias="from")
    to_note: str = Field(alias="to")
    type: str = "reference"

    model_config = {"populate_by_name": True}


class HierarchyEntry(BaseModel):
    """A node in the virtual hierarchy. id is 'label:Name' or 'note:id'."""
    id: str
    children: list[str] = Field(default_factory=list)


class GraphMOC(BaseModel):
    """The complete graph_moc.yaml schema."""
    version: float = 1.1
    hierarchy: list[HierarchyEntry] = Field(default_factory=list)
    edges: list[EdgeEntry] = Field(default_factory=list)
    # Deprecated, kept for migration
    labels: list[LabelEntry] = Field(default_factory=list)


# ──────────────────────────────────────────────
#  API request / response schemas
# ──────────────────────────────────────────────

class NoteCreate(BaseModel):
    """Request body for creating a note."""
    title: str = Field(..., min_length=1, max_length=200)
    content: str = ""
    labels: list[str] = Field(default_factory=list)


class NoteUpdate(BaseModel):
    """Request body for updating a note."""
    content: str | None = None
    labels: list[str] | None = None


class NoteRename(BaseModel):
    """Request body for renaming a note."""
    new_title: str = Field(..., min_length=1, max_length=200)


class NoteResponse(BaseModel):
    """Full note representation returned by the API."""
    id: str
    title: str
    content: str
    labels: list[str] = Field(default_factory=list)
    links: list[str] = Field(default_factory=list)
    attachments: list[str] = Field(default_factory=list)


class NoteSummary(BaseModel):
    """Lightweight note info for list views."""
    id: str
    title: str
    labels: list[str] = Field(default_factory=list)


class LabelCreate(BaseModel):
    """Create a new label."""
    name: str = Field(..., min_length=1, max_length=100)


class LabelMove(BaseModel):
    """Move a label subtree."""
    new_parent: str | None = None


class LabelUpdate(BaseModel):
    """Update label membership."""
    notes: list[str] = Field(default_factory=list)


class AttachmentResponse(BaseModel):
    """Attachment metadata."""
    filename: str
    size: int
    ref_count: int


class GraphNode(BaseModel):
    """A node in the graph visualization."""
    id: str
    title: str
    labels: list[str] = Field(default_factory=list)


class GraphEdge(BaseModel):
    """An edge in the graph visualization."""
    source: str
    target: str
    type: str = "reference"


class GraphData(BaseModel):
    """Full graph payload for visualization."""
    nodes: list[GraphNode] = Field(default_factory=list)
    edges: list[GraphEdge] = Field(default_factory=list)


# ──────────────────────────────────────────────
#  Vault structures
# ──────────────────────────────────────────────

class VaultInfo(BaseModel):
    """Information about a vault."""
    path: str
    name: str
    is_active: bool

class VaultSettings(BaseModel):
    """Global settings for Zenith."""
    active_vault: str | None = None
    vaults: list[str] = Field(default_factory=list)

class VaultCreate(BaseModel):
    """Request to create or open a vault."""
    path: str

