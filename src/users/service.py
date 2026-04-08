from sqlalchemy.ext.asyncio import AsyncSession
from src.users.models import User
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload
from fastapi import UploadFile, HTTPException
from src.calls.service import rooms
from src.calls.models import Call
from src.config import settings
from pathlib import Path
import shutil


async def get_users(
    user: User, db: AsyncSession, 
    page: int, limit: int
):
    offset = (page - 1) * limit
    result = await db.execute(
        select(User)
        .where(User.id != user.id)
        .offset(offset)
        .limit(limit)
    )
    return result.scalars().all()

async def get_connected_users(
    call_uuid: str, user: User, db: AsyncSession
):
    result = await db.execute(
        select(Call)
        .options(
            selectinload(Call.callees),
            selectinload(Call.caller)
        )
        .where(
            Call.uuid == call_uuid,
            or_(
                Call.callees.any(id=user.id),
                Call.caller_id == user.id
            )
        )
    )
    call = result.scalar_one_or_none()
    if not call:
        raise HTTPException(detail="Call not found.", status_code=404)
    
    if call_uuid not in rooms: return []

    user_ids = [
        item["user_id"]
        for item in rooms[call_uuid]
    ]

    if not user_ids: return []

    stmt = select(User).where(User.id.in_(user_ids))
    result = await db.execute(stmt)
    users = result.scalars().all()

    return users

async def get_search_users(q: str, user: User, db: AsyncSession):
    stmt = select(User).where(User.username.ilike(f"%{q}%"), User.id != user.id)
    result = await db.execute(stmt)
    users = result.scalars().all()
    return users

async def set_avatar(
    user: User, upload_file: UploadFile, db: AsyncSession
):    
    AVATAR_DIR = settings.avatar_dir
    AVATAR_DIR.mkdir(parents=True, exist_ok=True)

    ALLOWED_AVATAR_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
    ALLOWED_AVATAR_MIME_TYPES = {
        "image/jpeg",
        "image/png",
        "image/webp",
    }

    if Path(upload_file.filename).suffix.lower() not in ALLOWED_AVATAR_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Unsupported avatar format"
        )
    
    if upload_file.content_type not in ALLOWED_AVATAR_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Invalid avatar MIME type"
        )

    filename = f"{user.id}_{upload_file.filename}"
    file_path = AVATAR_DIR / filename
    try:
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(upload_file.file, buffer)
    finally:
        upload_file.file.close()

    if user.avatar:
        old_filename = user.avatar.replace(
            settings.avatar_dir_prefix, ""
        )
        old_file_path = AVATAR_DIR / old_filename

        if old_file_path.exists() and old_file_path.is_file():
            old_file_path.unlink()

    user.avatar = settings.avatar_dir_prefix + filename

    db.add(user)
    await db.commit()
    await db.refresh(user)

    return {"detail": "Success."}
