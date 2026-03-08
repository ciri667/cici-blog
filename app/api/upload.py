import uuid
from datetime import datetime, timezone

import boto3
from fastapi import APIRouter, Depends, HTTPException, UploadFile

from app.core.config import settings
from app.core.deps import require_admin
from app.models.user import User

router = APIRouter(prefix="/upload", tags=["upload"])

ALLOWED_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}
MAX_SIZE = 10 * 1024 * 1024  # 10MB


def _get_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=f"https://{settings.R2_ACCOUNT_ID}.r2.cloudflarestorage.com",
        aws_access_key_id=settings.R2_ACCESS_KEY_ID,
        aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
        region_name="auto",
    )


@router.post("")
async def upload_image(
    file: UploadFile,
    admin: User = Depends(require_admin),
):
    # Validate content type
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型: {file.content_type}，仅支持 JPG/PNG/WebP/GIF",
        )

    # Read file and validate size
    data = await file.read()
    if len(data) > MAX_SIZE:
        raise HTTPException(status_code=400, detail="文件大小不能超过 10MB")

    # Generate storage path: blog/year/month/uuid.ext
    now = datetime.now(timezone.utc)
    ext = ALLOWED_TYPES[file.content_type]
    filename = f"{uuid.uuid4().hex}{ext}"
    key = f"blog/{now.year}/{now.month:02d}/{filename}"

    # Upload to R2
    s3 = _get_s3_client()
    s3.put_object(
        Bucket=settings.R2_BUCKET_NAME,
        Key=key,
        Body=data,
        ContentType=file.content_type,
    )

    cdn_url = f"{settings.R2_CDN_URL.rstrip('/')}/{key}"
    return {"url": cdn_url}
