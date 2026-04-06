from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaRelay
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
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
        "transceiver": audio_transceiver,
        "user_id": user.id
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

async def remove_peer_service(request: Request, user: User):
    data = await request.json()
    call_id = data["call_id"]

    if call_id in rooms:
        peer_to_remove = None

        for peer in rooms[call_id]:
            if peer["user_id"] == user.id:
                peer_to_remove = peer
                break

        if peer_to_remove:
            pc = peer_to_remove["pc"]

            for peer in rooms[call_id]:
                if peer["pc"] != pc:
                    peer["transceiver"].sender.replaceTrack(None)

            rooms[call_id] = [
                peer for peer in rooms[call_id]
                if peer["pc"] != pc
            ]

            print(f"[{call_id}] peer disconnected, remaining:", len(rooms[call_id]))

            if not rooms[call_id]: del rooms[call_id]

            await pc.close()

            return {"detail": "Success."}
    
    raise HTTPException(detail="Peer not found.", status_code=404)

async def get_my_calls(user: User, db: AsyncSession):
    result = await db.execute(
        select(Call).where(Call.caller_id == user.id)
        .options(selectinload(Call.callees))
    )
    calls = result.scalars().all()
    return calls

async def get_connected_calls(user: User, db: AsyncSession):
    result = await db.execute(
        select(Call)
        .options(
            selectinload(Call.callees),
            selectinload(Call.caller)
        )
        .where(Call.callees.any(id=user.id))
    )
    calls = result.scalars().all()
    return calls

async def get_call(
    call_id: int, user: User, db: AsyncSession      
):
    result = await db.execute(
        select(Call).where(
            Call.caller_id == user.id,
            Call.id == call_id
        ).options(selectinload(Call.callees))
    )
    call = result.scalar_one_or_none()
    if not call:
        raise HTTPException(
            detail="Call not found.", status_code=404
        )
    return call

async def create_call_service(
    data: CallCreate, user: User, db: AsyncSession
):    
    call = Call(caller_id=user.id, title=data.title)

    db.add(call)
    await db.commit()
    await db.refresh(call)

    return call

async def delete_call_service(
    call_id: int, user: User, db: AsyncSession
):
    result = await db.execute(
        select(Call).where(
            Call.id == call_id,
            Call.caller_id == user.id
        )
    )
    call = result.scalar_one_or_none()
    if not call:
        raise HTTPException(
            detail="Call not found.", status_code=404
        )

    await db.delete(call)
    await db.commit()

    return {"detail": "Success."}

async def add_user_to_call(
    data: CalleeSchema, user: User, db: AsyncSession
):
    callee, call = await get_user_and_call(data, user, db)
    
    if callee in call.callees:
        return JSONResponse(
            content={"detail": "User already in call"}, status_code=208
        )

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
