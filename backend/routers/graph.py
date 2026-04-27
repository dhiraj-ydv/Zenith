"""
Graph Router — Graph visualization data and LLM-friendly index endpoint.
"""

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

from models import GraphData
from services.graph import GraphService
from services.moc import MOCService

router = APIRouter(prefix="/api/graph", tags=["Graph"])

graph_service: GraphService = None  # type: ignore
moc_service: MOCService = None  # type: ignore


@router.get("/data", response_model=GraphData)
async def get_graph_data(id: str | None = None):
    """Get the full graph for visualization (nodes + edges). Optional id filters for Canvas."""
    return graph_service.build_graph(id)


@router.get("/index", response_class=PlainTextResponse)
async def get_graph_index():
    """Return the raw graph_moc.yaml content (LLM-friendly)."""
    return moc_service.get_raw_yaml()
