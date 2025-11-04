# backend/modal_runtime/tools.py
import hashlib
import mimetypes
from pathlib import Path
import os
from typing import List, Dict, Any

import modal
import pandas as pd

# Import the Modal app from app.py
# note: since we import like this, we need to deploy with: modal deploy -m backend.modal_runtime.functions
from .app import app, image
from .session import volume_name
WORKSPACE_VOLUME = modal.Volume.from_name(volume_name(), create_if_missing=True)

def _walk_files(base: Path, exts: set) -> List[Path]:
    files = []
    if base.exists():
        for p in base.rglob("*"):
            if p.is_file() and (not exts or p.suffix.lower() in exts):
                files.append(p)
    return files

def _session_base(session_id: str) -> Path:
    """Resolve per-session base dir; session_id must be provided by caller."""
    return Path("/workspace") / "sessions" / session_id

@app.function(
    image=image,
    volumes={"/workspace": WORKSPACE_VOLUME},
    timeout=60,
)
def list_loaded_datasets(
    session_id: str,
    subdir: str = "datasets"
) -> List[Dict[str, Any]]:
    """
    List datasets in the workspace. Return structured metadata.
    """
    base = _session_base(session_id) / subdir

    exts = {".csv", ".parquet", ".xlsx", ".xls"}
    out: List[Dict[str, Any]] = []
    for p in _walk_files(base, exts):
        stat = p.stat()
        rel = str(p.relative_to(base))
        out.append({
            "path": rel,
            "size_bytes": stat.st_size,
            "size_mb": round(stat.st_size / (1024 * 1024), 3),
            "mtime": stat.st_mtime,
            "mime": mimetypes.guess_type(p.name)[0] or "application/octet-stream",
        })
    return out

# Accept dataset bytes from backend and persist into the sandbox, returning summary
@app.function(
    image=image,
    volumes={"/workspace": WORKSPACE_VOLUME},
    timeout=180,
)
def write_dataset_bytes(
    dataset_id: str,
    data_b64: str,
    session_id: str,
    ext: str = "parquet",
    subdir: str = "datasets",
) -> Dict[str, Any]:
    import base64

    data = base64.b64decode(data_b64)
    base_dir = _session_base(session_id)
    datasets_dir = base_dir / subdir
    datasets_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{dataset_id}.{ext.lstrip('.')}"
    path = datasets_dir / filename
    path.write_bytes(data)

    mime = mimetypes.guess_type(filename)[0] or "application/octet-stream"
    size = path.stat().st_size

    summary: Dict[str, Any] = {
        "dataset_id": dataset_id,
        "path": str(path),
        "rel_path": str(path.relative_to(base_dir)),
        "mime": mime,
        "size_bytes": size,
        "size_mb": round(size / (1024 * 1024), 3),
        "ext": ext.lower(),
    }

    return summary   

# --------------------- (!) Deprecated (!) ---------------------
# NOTE: this function is actually useless when we need to export from a running sandbox: 
# Modal volumes do not sync to outside functions unless we terminate the sandbox (which defeats the purpose of the sandbox)
# we leave it for legacy reasons, but it is not used in the new codebase.
@app.function(
    image=image,
    volumes={"/workspace": WORKSPACE_VOLUME},
    timeout=180,
    secrets=[modal.Secret.from_name("aws-credentials-IAM")],  # store AWS creds in Modal
)
def export_dataset(
    dataset_path: str,
    bucket: str,
    session_id: str
) -> Dict[str, Any]:
    """
    Upload a file from the Modal workspace to S3 and return metadata.
    """
    import boto3
    import time

    base = _session_base(session_id)
    full = base / dataset_path
    
    # Retry logic to handle volume sync delays
    # Files created in sandbox take time to sync to volume before being visible to other functions
    max_retries = 20  # up to ~10s to allow Volume sync
    for attempt in range(max_retries):
        if full.exists():
            break
        if attempt < max_retries - 1:
            time.sleep(0.5)
    else:
        return {"error": f"File not found after {max_retries * 0.5}s (volume sync timeout): {dataset_path}"}

    try:
        data = full.read_bytes()
        sha256 = hashlib.sha256(data).hexdigest()
        mime = mimetypes.guess_type(full.name)[0] or "application/octet-stream"
        size = len(data)

        # Datasets exported under a separate prefix
        s3_key = f"output/datasets/{sha256[:2]}/{sha256[2:4]}/{sha256}"
        
        from botocore.client import Config
        region = os.getenv("AWS_REGION", "eu-central-1")
        s3_client = boto3.client(
            "s3",
            region_name=region,
            config=Config(signature_version='s3v4')
        )
        s3_client.put_object(
            Bucket=bucket,
            Key=s3_key,
            Body=data,
            ContentType=mime,
        )

        return {
            "name": full.name,
            "path": str(full),
            "sha256": sha256,
            "mime": mime,
            "size": size,
            "s3_key": s3_key,
            "s3_url": f"s3://{bucket}/{s3_key}",
        }
    except Exception as e:
        return {"error": f"S3 upload failed: {e}"}