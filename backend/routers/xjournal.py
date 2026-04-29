from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import FileResponse
import os
import gzip
import subprocess
from pathlib import Path
from services.notes import NoteService

router = APIRouter(prefix="/api/xjournal", tags=["Xjournal"])

# This will be injected in main.py
note_service: NoteService = None  # type: ignore

def get_xournalpp_cmd():
    """Get the command to run Xournal++, with fallbacks for Windows."""
    if os.name == 'nt':
        common_paths = [
            Path("C:/Program Files/Xournal++/bin/xournalpp.exe"),
            Path("C:/Program Files (x86)/Xournal++/bin/xournalpp.exe"),
        ]
        for p in common_paths:
            if p.exists():
                return str(p)
    return "xournalpp"

@router.post("/{note_id}/open")
async def open_xjournal(note_id: str):
    """Open the .xopp file in the system's default Xournal++ application."""
    if note_service is None:
        raise HTTPException(status_code=500, detail="Note service not initialized")
        
    path, note_type = note_service._find_note_file(note_id)
    if not path or note_type != "xopp":
        raise HTTPException(status_code=404, detail="Xjournal note not found")
    
    try:
        if os.name == 'nt':  # Windows
            try:
                os.startfile(str(path))
            except Exception:
                cmd = get_xournalpp_cmd()
                subprocess.Popen([cmd, str(path)])
        else:  # Linux / macOS
            try:
                subprocess.Popen(['xdg-open', str(path)])
            except Exception:
                try:
                    subprocess.Popen(['open', str(path)])
                except Exception:
                    subprocess.Popen(['xournalpp', str(path)])
        return {"status": "success", "message": f"Opened {note_id} in Xournal++"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to open Xournal++: {str(e)}")

@router.get("/{note_id}/xml")
async def get_xjournal_xml(note_id: str):
    """Return the raw XML content of the .xopp file (decompressed if gzipped).
    
    This allows the frontend to parse and render strokes directly in the browser,
    ensuring the preview always reflects the latest file state on disk.
    """
    if note_service is None:
        raise HTTPException(status_code=500, detail="Note service not initialized")

    path, note_type = note_service._find_note_file(note_id)
    if not path or note_type != "xopp":
        raise HTTPException(status_code=404, detail="Xjournal note not found")

    try:
        raw = path.read_bytes()

        # Detect gzip: magic bytes 0x1F 0x8B
        if len(raw) >= 2 and raw[0] == 0x1F and raw[1] == 0x8B:
            xml_content = gzip.decompress(raw).decode("utf-8")
        else:
            xml_content = raw.decode("utf-8")

        return Response(content=xml_content, media_type="application/xml")
    except Exception as e:
        print(f"Zenith: Failed to read xopp {note_id}: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to read .xopp file: {str(e)}")

@router.get("/{note_id}/file-info")
async def get_xjournal_file_info(note_id: str):
    """Return file metadata (modification time, size) for cache-busting / polling."""
    if note_service is None:
        raise HTTPException(status_code=500, detail="Note service not initialized")

    path, note_type = note_service._find_note_file(note_id)
    if not path or note_type != "xopp":
        raise HTTPException(status_code=404, detail="Xjournal note not found")

    stat = path.stat()
    return {
        "note_id": note_id,
        "size": stat.st_size,
        "modified": stat.st_mtime,
    }
