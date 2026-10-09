import mimetypes
import uuid
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.media import MediaAsset
from app.services.catalog import public_media_url

STORAGE_ROOT = Path(__file__).resolve().parents[2] / "storage"


def guess_content_type(path: Path) -> str:
    guessed, _ = mimetypes.guess_type(str(path))
    return guessed or "application/octet-stream"


def save_media_file(
    db: Session,
    *,
    kind: str,
    source_path: str | Path,
    filename: str | None = None,
) -> tuple[str, str]:
    """Copy a local file into durable storage (disk + postgres) and return (url, filename)."""
    source = Path(source_path)
    if not source.exists() or not source.is_file():
        raise FileNotFoundError(f"Media source missing: {source}")

    suffix = source.suffix or ".bin"
    safe_name = filename or f"{uuid.uuid4().hex}{suffix}"
    safe_name = Path(safe_name).name
    dest_dir = STORAGE_ROOT / kind
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / safe_name
    data = source.read_bytes()
    dest.write_bytes(data)

    content_type = guess_content_type(dest)
    existing = db.scalar(
        select(MediaAsset).where(
            MediaAsset.kind == kind, MediaAsset.filename == safe_name
        )
    )
    if existing:
        existing.data = data
        existing.content_type = content_type
    else:
        db.add(
            MediaAsset(
                kind=kind,
                filename=safe_name,
                content_type=content_type,
                data=data,
            )
        )
    db.commit()
    return public_media_url(kind, safe_name), safe_name


def load_media(db: Session, *, kind: str, filename: str) -> tuple[bytes, str] | None:
    safe_name = Path(filename).name
    disk_path = (STORAGE_ROOT / kind / safe_name).resolve()
    root = (STORAGE_ROOT / kind).resolve()
    if str(disk_path).startswith(str(root)) and disk_path.exists() and disk_path.is_file():
        return disk_path.read_bytes(), guess_content_type(disk_path)

    asset = db.scalar(
        select(MediaAsset).where(
            MediaAsset.kind == kind, MediaAsset.filename == safe_name
        )
    )
    if not asset:
        return None

    # Rebuild disk cache after redeploy.
    try:
        root.mkdir(parents=True, exist_ok=True)
        disk_path.write_bytes(asset.data)
    except OSError:
        pass
    return asset.data, asset.content_type
