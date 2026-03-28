from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaRelay
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select
from fastapi import Request, HTTPException
from src.users.models import User
from src.calls.models import Call
from src.calls.denoise import FrameSplitterTrack
from src.calls.schemas import CalleeSchema, CallCreate
from src.calls.utils import get_user_and_call


relay: MediaRelay = MediaRelay()
rooms: dict[str, list] = {}

async def set_offer(
    request: Request, user: User, db: AsyncSession
):
    data = await request.json()
    call_id = data["call_id"]

    result = await db.execute(
        select(Call).where(Call.uuid == call_id)
    )
    call = result.scalar_one_or_none()

    if call is None:
        raise HTTPException(
            status_code=404, detail="Call not found"
        )

    if user.id != call.caller_id and user not in call.callees:
        raise HTTPException(
            status_code=403, detail="Forbidden."
        )

    pc = RTCPeerConnection()

    audio_transceiver = pc.addTransceiver(
        "audio",
        direction="sendrecv"
    )

    rooms.setdefault(call_id, []).append({
        "pc": pc,
        "transceiver": audio_transceiver
    })

    print(f"[{call_id}] peer connected, total:", len(rooms[call_id]))

    @pc.on("track")
    def on_track(track):
        if track.kind != "audio":
            return

        print(f"[{call_id}] audio track received")

        track = FrameSplitterTrack(track)
        relayed = relay.subscribe(track)

        for peer in rooms[call_id]:
            if peer["pc"] != pc:
                peer["transceiver"].sender.replaceTrack(relayed)

    await pc.setRemoteDescription(
        RTCSessionDescription(
            sdp=data["sdp"],
            type=data["type"]
        )
    )

    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    return {
        "sdp": pc.localDescription.sdp,
        "type": pc.localDescription.type
    }

async def get_my_calls(user: User, db: AsyncSession):
    result = await db.execute(
        select(Call).where(Call.caller_id == user.id)
        .options(selectinload(Call.callees))
    )
    calls = result.scalars().all()
    return calls

async def create_call(
    data: CallCreate, user: User, db: AsyncSession
):    
    call = Call(caller_id=user.id, is_private=data.is_private)

    db.add(call)
    await db.commit()
    await db.refresh(call)

    return call

async def add_user_to_call(
    data: CalleeSchema, user: User, db: AsyncSession
):
    callee, call = await get_user_and_call(data, user, db)
    
    if callee not in call.callees:
        call.callees.append(callee)
        db.add(call)
        await db.commit()
        await db.refresh(call)

    return call

async def remove_user_from_call(
    data: CalleeSchema, user: User, db: AsyncSession
):
    callee, call = await get_user_and_call(data, user, db)
    
    if callee in call.callees:
        call.callees.remove(callee)
        db.add(call)
        await db.commit()
        await db.refresh(call)

    return call
