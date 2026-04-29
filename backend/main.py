"""
Zenith — Main FastAPI Application
A local-first, opinionated note-taking web application.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import HOST, PORT, CORS_ORIGINS
from services.vault import VaultManager
from services.moc import MOCService
from services.attachments import AttachmentService
from services.notes import NoteService
from services.graph import GraphService
from routers import vaults as vaults_router
from routers import notes as notes_router
from routers import labels as labels_router
from routers import attachments as attachments_router
from routers import graph as graph_router
from routers import lorien as lorien_router
from routers import xjournal as xjournal_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup / shutdown lifecycle."""
    # ── Startup ──
    vault_manager = VaultManager()
    vault_manager.init_vault()

    # Initialize services
    moc = MOCService(vault_manager)
    moc.load()

    attach = AttachmentService(vault_manager)
    attach.rebuild_counts()

    note_svc = NoteService(moc, attach, vault_manager)
    graph_svc = GraphService(moc, vault_manager)

    # Inject services into routers
    vaults_router.router.vault_manager = vault_manager
    vaults_router.router.moc_service = moc
    vaults_router.router.attachment_service = attach
    
    notes_router.note_service = note_svc
    xjournal_router.note_service = note_svc
    labels_router.moc_service = moc
    attachments_router.attachment_service = attach
    graph_router.graph_service = graph_svc
    graph_router.moc_service = moc

    print("[OK] Zenith is ready")
    yield
    # ── Shutdown ──
    print("[--] Zenith shutting down")


app = FastAPI(
    title="Zenith",
    description="Local-first, opinionated note-taking for personal knowledge management.",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(vaults_router.router)
app.include_router(notes_router.router)
app.include_router(labels_router.router)
app.include_router(attachments_router.router)
app.include_router(graph_router.router)
app.include_router(lorien_router.router)
app.include_router(xjournal_router.router)


@app.get("/")
async def root():
    return {"name": "Zenith", "version": "0.1.0", "status": "running"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=HOST, port=PORT, reload=True)
