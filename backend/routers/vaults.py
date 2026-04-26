"""
Vaults Router — Manage the active vault and create new vaults.
"""

from pathlib import Path
from fastapi import APIRouter, HTTPException

from models import VaultInfo, VaultCreate, VaultSettings
from services.vault import VaultManager
from services.moc import MOCService
from services.attachments import AttachmentService


router = APIRouter(prefix="/api/vaults", tags=["Vaults"])

# The services will be injected via request state or global
router.vault_manager: VaultManager | None = None
router.moc_service: MOCService | None = None
router.attachment_service: AttachmentService | None = None


def get_manager() -> VaultManager:
    if not router.vault_manager:
        raise RuntimeError("VaultManager not initialized")
    return router.vault_manager

def reload_services() -> None:
    if router.moc_service:
        router.moc_service.load()
    if router.attachment_service:
        router.attachment_service.rebuild_counts()


@router.get("", response_model=list[VaultInfo])
def list_vaults() -> list[VaultInfo]:
    """List all known vaults and indicate the active one."""
    manager = get_manager()
    active = manager.get_active_vault()
    vaults = []
    
    for path in manager.get_vaults():
        try:
            name = Path(path).name
            vaults.append(VaultInfo(
                path=path,
                name=name,
                is_active=(path == active)
            ))
        except Exception:
            continue
            
    return vaults


@router.get("/active", response_model=VaultInfo | None)
def get_active_vault() -> VaultInfo | None:
    """Get the currently active vault."""
    manager = get_manager()
    active = manager.get_active_vault()
    if not active:
        return None
    return VaultInfo(
        path=active,
        name=Path(active).name,
        is_active=True
    )


@router.post("", response_model=VaultInfo)
def create_or_open_vault(req: VaultCreate) -> VaultInfo:
    """Create a new vault or open an existing one, making it active."""
    manager = get_manager()
    path = req.path
    if not path:
        raise HTTPException(status_code=400, detail="Path cannot be empty")
        
    try:
        manager.set_active_vault(path)
        reload_services()
        return VaultInfo(
            path=path,
            name=Path(path).name,
            is_active=True
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("", status_code=204)
def remove_vault(path: str) -> None:
    """Remove a vault from the known list (does not delete files)."""
    manager = get_manager()
    manager.remove_vault(path)
