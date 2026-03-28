from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException
from typing import Tuple
from src.users.models import User
from src.calls.models import Call
from src.calls.schemas import CalleeSchema


async def get_user_and_call(
    data: CalleeSchema, 
    user: User, 
    db: AsyncSession
) -> Tuple:
    result = await db.execute(
        select(User).where(User.id == data.callee_id)
    )
    callee = result.scalar_one_or_none()
    if not callee:
        raise HTTPException(
            status_code=404, detail="User not found."
        )
    
    result = await db.execute(
        select(Call).where(Call.id == data.call_id, user.id == Call.caller_id)
        .options(selectinload(Call.callees)) 
    )
    call = result.scalar_one_or_none()
    if not call:
        raise HTTPException(
            status_code=404, detail="Call not found."
        )
    
    return callee, call
