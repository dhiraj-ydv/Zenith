from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
import os

router = APIRouter(prefix="/lorien", tags=["Lorien"])

# Path to the Lorien HTML5 bundle
BUNDLE_DIR = Path(__file__).parent.parent / "lorien_bundle"

@router.get("/{path:path}")
async def serve_lorien(path: str):
    if not path or path == "/":
        path = "index.html"
    
    file_path = BUNDLE_DIR / path
    if not file_path.exists() or not file_path.is_file():
        # Fallback to index.html for SPA-like behavior if needed, 
        # but Godot bundles usually need specific files.
        if path == "index.html":
             raise HTTPException(status_code=404, detail="Lorien bundle not found. Please ensure backend/lorien_bundle is populated.")
        raise HTTPException(status_code=404, detail="File not found")

    # Godot HTML5 exports (especially with threads) require COOP/COEP headers
    headers = {
        "Cross-Origin-Opener-Policy": "same-origin",
        "Cross-Origin-Embedder-Policy": "require-corp",
        "Access-Control-Allow-Origin": "*",
    }
    
    return FileResponse(file_path, headers=headers)
