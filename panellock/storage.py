import os
import base64
import uuid
from datetime import date, timedelta
from pathlib import Path

import boto3
from django.conf import settings

from .models import BackupAsset


ALLOWED_BACKUP_EXTENSIONS = {".gwbk", ".zip", ".mer", ".apa", ".acd", ".json", ".xml", ".yaml", ".yml"}


def create_upload(*, organization, panel, user, filename, size_bytes, sha256):
    sha256 = sha256.lower()
    extension = Path(filename).suffix.lower()
    if extension not in ALLOWED_BACKUP_EXTENSIONS:
        raise ValueError("Unsupported backup format.")
    if size_bytes <= 0 or size_bytes > settings.PANELLOCK_UPLOAD_MAX_BYTES:
        raise ValueError("Backup exceeds the 10 GiB object limit.")
    try:
        raw_checksum = bytes.fromhex(sha256)
    except ValueError as exc:
        raise ValueError("A valid SHA-256 checksum is required.") from exc
    if len(raw_checksum) != 32:
        raise ValueError("A valid SHA-256 checksum is required.")
    location = settings.PANELLOCK_S3_LOCATIONS.get(organization.data_region, {})
    bucket = location.get("bucket")
    region = location.get("region")
    if not bucket or not region:
        raise ValueError(f"Private backup storage is not configured for {organization.get_data_region_display()}.")

    object_key = f"quarantine/{organization.id}/{panel.id}/{uuid.uuid4()}{extension}"
    backup = BackupAsset.objects.create(
        organization=organization,
        panel=panel,
        uploaded_by=user,
        original_filename=os.path.basename(filename),
        object_key=object_key,
        size_bytes=size_bytes,
        sha256=sha256,
        retention_until=date.today() + timedelta(days=90),
    )
    checksum_b64 = base64.b64encode(raw_checksum).decode()
    client = boto3.client("s3", region_name=region)
    post = client.generate_presigned_post(
        Bucket=bucket,
        Key=object_key,
        Fields={
            "Content-Type": "application/octet-stream",
            "x-amz-server-side-encryption": "AES256",
            "x-amz-checksum-sha256": checksum_b64,
        },
        Conditions=[
            {"Content-Type": "application/octet-stream"},
            {"x-amz-server-side-encryption": "AES256"},
            {"x-amz-checksum-sha256": checksum_b64},
            ["content-length-range", size_bytes, size_bytes],
        ],
        ExpiresIn=900,
    )
    return {"backup_id": str(backup.id), "upload": post, "expires_in": 900}
