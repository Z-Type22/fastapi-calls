from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaRelay
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import Request, HTTPException
from src.users.models import User
from src.calls.schemas import CallCreate
from src.calls.models import Call


relay: MediaRelay = MediaRelay()
rooms: dict[str, list] = {}

async def set_offer(request: Request):
    data = await request.json()
    call_id = data["call_id"]

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

async def create_call(
    call: CallCreate, user: User, db: AsyncSession
):
    result = await db.execute(
        select(User).where(User.id == call.callee_id)
    )
    callee = result.scalar_one_or_none()

    if not callee:
        raise HTTPException(
            status_code=404, detail="User not found"
        )

    if call.callee_id == user.id:
        raise HTTPException(
            status_code=403, detail="You cannot call yourself."
        )
    
    call = Call(
        caller_id=user.id,
        callee_id=call.callee_id,
        status=Call.Status.RINGING,
    )

    db.add(call)
    await db.commit()
    await db.refresh(call)

    return call

async def accepting_call(
    call_id: int, user: User, 
    db: AsyncSession, accept: bool
):
    result = await db.execute(
        select(Call).where(
            Call.id == call_id,
            Call.status.in_([
                Call.Status.CREATED,
                Call.Status.RINGING,
            ])
        )
    )
    call = result.scalar_one_or_none()

    if not call:
        raise HTTPException(
            status_code=404, detail="Call not found"
        )
    
    if call.callee_id != user.id:
        raise HTTPException(
            status_code=403, detail="Forbidden"
        )
    
    if accept:
        call.status = Call.Status.ACCEPTED
        status = "accepted"
    else:
        call.status = Call.Status.REJECTED
        status = "rejected"

    await db.commit()

    return {"detail": f"Call {status}"}

async def end_call(
    call_id: int, user: User, db: AsyncSession,
):
    result = await db.execute(
        select(Call).where(
            Call.id == call_id,
            Call.status.in_([Call.Status.ACCEPTED])
        )
    )
    call = result.scalar_one_or_none()

    if not call:
        raise HTTPException(
            status_code=404, detail="Call not found"
        )
    
    if user.id not in [call.callee_id, call.caller_id]:
        raise HTTPException(
            status_code=403, detail="Forbidden"
        )
    
    call.status = Call.Status.ENDED
    await db.commit()

    return {"detail": "Call ended."}
