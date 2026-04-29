"""
Attachments Router — Upload, list, serve, and garbage-collect attachments.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import FileResponse, Response

from models import AttachmentResponse
from services.attachments import AttachmentService

router = APIRouter(prefix="/api/attachments", tags=["Attachments"])

attachment_service: AttachmentService = None  # type: ignore


@router.get("", response_model=list[AttachmentResponse])
async def list_attachments():
    """List all attachments with reference counts."""
    items = attachment_service.list_attachments()
    return [AttachmentResponse(**item) for item in items]


@router.post("", status_code=201)
async def upload_attachment(file: UploadFile = File(...)):
    """Upload a file to /attachments."""
    data = await file.read()
    filename = attachment_service.save_attachment(file.filename or "upload", data)
    return {"filename": filename, "size": len(data)}


@router.get("/{filename}")
async def get_attachment(filename: str):
    """Serve an attachment file."""
    path = attachment_service.get_attachment_path(filename)
    if not path:
        raise HTTPException(status_code=404, detail="Attachment not found")
    # Explicitly add CORS header and inline content-disposition to encourage in-browser rendering
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Content-Disposition": f"inline; filename=\"{path.name}\"",
    }
    return FileResponse(path, headers=headers)


@router.head("/{filename}")
async def head_attachment(filename: str):
    """HEAD for attachment - return headers for the file without body."""
    path = attachment_service.get_attachment_path(filename)
    if not path:
        raise HTTPException(status_code=404, detail="Attachment not found")
    stat = path.stat()
    headers = {
        "Content-Length": str(stat.st_size),
        "Content-Type": "application/pdf" if path.suffix.lower() == ".pdf" else "application/octet-stream",
        "Accept-Ranges": "bytes",
        "Access-Control-Allow-Origin": "*",
        "Content-Disposition": f"inline; filename=\"{path.name}\"",
    }
    return Response(status_code=200, headers=headers)


@router.post("/gc")
async def run_gc():
    """Manually trigger garbage collection."""
    deleted = attachment_service.run_full_gc()
    return {"deleted": deleted, "count": len(deleted)}
