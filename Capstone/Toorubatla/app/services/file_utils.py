import hashlib, mimetypes
from pathlib import Path

SUPPORTED={".pdf", ".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".csv"}
def sha256_file(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024*1024), b""): h.update(chunk)
    return h.hexdigest()
def mime_type(path: Path) -> str:
    return mimetypes.guess_type(path.name)[0] or "application/octet-stream"
def validate_path(path: Path) -> None:
    if path.suffix.lower() not in SUPPORTED: raise ValueError(f"Unsupported extension: {path.suffix}")
    if not path.is_file(): raise ValueError("Input is not a file")
