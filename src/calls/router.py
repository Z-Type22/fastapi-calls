from fastapi import APIRouter, Request, Depends
from src.auth.jwt_service import authorize
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_db
from src.calls.service import (
    set_offer, 
    create_call,
    accepting_call,
    end_call
)
from src.calls.schemas import (
    CallCreate, CallRead, Message
)
from src.users.models import User


router = APIRouter()

@router.post("/offer")
async def offer(
    request: Request, 
    user: User = Depends(authorize),
    db: AsyncSession = Depends(get_db),
):
    return await set_offer(request, user, db)

@router.post("/create", response_model=CallRead)
async def create(
    call: CallCreate,
    user: User = Depends(authorize),
    db: AsyncSession = Depends(get_db),
):
    return await create_call(call, user, db)

@router.post("/accept/{call_id}", response_model=Message)
async def accept(
    call_id: int,
    user: User = Depends(authorize),
    db: AsyncSession = Depends(get_db),
):
    return await accepting_call(call_id, user, db, accept=True)

@router.post("/reject/{call_id}", response_model=Message)
async def reject(
    call_id: int,
    user: User = Depends(authorize),
    db: AsyncSession = Depends(get_db)
):
    return await accepting_call(call_id, user, db, accept=False)

@router.post("/end/{call_id}", response_model=Message)
async def end(
    call_id: int,
    user: User = Depends(authorize),
    db: AsyncSession = Depends(get_db)
):
    return await end_call(call_id, user, db)
