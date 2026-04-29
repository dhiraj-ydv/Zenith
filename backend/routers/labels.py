"""
Labels Router — Manage virtual folders (labels) in the MOC.
"""

from fastapi import APIRouter, HTTPException

from models import LabelCreate, LabelMove, LabelReorder, HierarchyEntry
from services.moc import MOCService

router = APIRouter(prefix="/api/labels", tags=["Labels"])

moc_service: MOCService = None  # type: ignore


@router.get("", response_model=list[HierarchyEntry])
async def list_labels():
    """List all hierarchy nodes."""
    moc = moc_service.get()
    return moc.hierarchy


@router.post("", response_model=dict, status_code=201)
async def create_label(body: LabelCreate):
    """Create a new feed or label. Expects full prefixed ID in body.name."""
    node_id = body.name
    
    # If no prefix provided, default to label:
    if ":" not in node_id:
        node_id = f"label:{node_id}"
    
    moc_service.add_to_hierarchy(node_id, body.parent)
    name = node_id.split(":", 1)[1]
    return {"id": node_id, "name": name}


@router.post("/{node_id}/move", status_code=200)
async def move_node(node_id: str, body: LabelMove):
    """Move a node in the hierarchy."""
    moc_service.move_node(node_id, body.new_parent)
    return {"status": "ok"}


@router.post("/{node_id}/reorder", status_code=200)
async def reorder_node(node_id: str, body: LabelReorder):
    """Reorder a node among its siblings."""
    moc_service.reorder_node(node_id, body.parent_id, body.index)
    return {"status": "ok"}


@router.delete("/{node_id}", status_code=204)
async def delete_node(node_id: str):
    """Delete a node from hierarchy."""
    moc_service.remove_from_hierarchy(node_id)
