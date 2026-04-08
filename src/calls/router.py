from fastapi import APIRouter, WebSocket, Depends
from src.auth.jwt_service import authorize
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_db
from src.calls.service import (
    set_offer,
    get_my_calls,
    create_call_service,
    add_user_to_call,
    remove_user_from_call,
    get_call,
    delete_call_service,
    get_invited_calls
)
from src.calls.schemas import (
    CallRead, CalleeSchema, Message, CallCreate
)
from src.users.models import User


router = APIRouter()

@router.get("/", response_model=list[CallRead])
async def read_calls(
    user: User = Depends(authorize),
    db: AsyncSession = Depends(get_db)
):
    return await get_my_calls(user, db)

@router.get("/invited", response_model=list[CallRead])
async def invited_calls(
    user: User = Depends(authorize),
    db: AsyncSession = Depends(get_db)
):
    return await get_invited_calls(user, db)

@router.get("/{call_id}", response_model=CallRead)
async def retrieve_call(
    call_id: int,
    user: User = Depends(authorize),
    db: AsyncSession = Depends(get_db)
):
    return await get_call(call_id, user, db)

@router.post("/", response_model=CallRead)
async def create_call(
    data: CallCreate,
    user: User = Depends(authorize),
    db: AsyncSession = Depends(get_db),
):
    return await create_call_service(data, user, db)

@router.delete("/{call_id}", response_model=Message)
async def delete_call(
    call_id: int,
    user: User = Depends(authorize),
    db: AsyncSession = Depends(get_db)
):
    return await delete_call_service(call_id, user, db)

@router.post("/add_callee", response_model=CallRead)
async def add_callee(
    data: CalleeSchema,
    user: User = Depends(authorize),
    db: AsyncSession = Depends(get_db),
):
    return await add_user_to_call(data, user, db)

@router.post("/remove_callee", response_model=CallRead)
async def remove_callee(
    data: CalleeSchema,
    user: User = Depends(authorize),
    db: AsyncSession = Depends(get_db),
):
    return await remove_user_from_call(data, user, db)

@router.websocket("/offer")
async def offer(
    websocket: WebSocket, 
    user: User = Depends(authorize),
    db: AsyncSession = Depends(get_db),
):
    return await set_offer(websocket, user, db)
