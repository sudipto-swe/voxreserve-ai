import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.entities import Conversation, Message
from app.agents.orchestrator import AgentOrchestrator

logger = logging.getLogger(__name__)
ws_router = APIRouter()


@ws_router.websocket("/ws/conversation/{conversation_id}")
async def websocket_conversation_endpoint(
    websocket: WebSocket,
    conversation_id: str,
    db: Session = Depends(get_db)
):
    """
    Real-time bidirectional WebSocket channel for Voice & Text Agent interactions.
    Streams transcription, thinking state, tool invocations, audio synthesis triggers, and results.
    """
    await websocket.accept()

    # Ensure conversation entity exists in DB
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        conv = Conversation(id=conversation_id)
        db.add(conv)
        db.commit()

    orchestrator = AgentOrchestrator(db=db, conversation_id=conversation_id)

    try:
        # Send initial connected greeting
        await websocket.send_json({
            "type": "connection_established",
            "conversation_id": conversation_id,
            "status": "ready",
            "message": "Connected to VoxReserve Voice & Reservation Engine."
        })

        while True:
            raw_data = await websocket.receive_text()
            data = json.loads(raw_data)
            event_type = data.get("type", "user_message")

            if event_type == "ping":
                await websocket.send_json({"type": "pong"})
                continue

            elif event_type in ["user_message", "user_transcript"]:
                user_text = data.get("content", "").strip()
                is_audio = data.get("is_audio", False)
                if not user_text:
                    continue

                # Persist user message
                user_msg = Message(
                    conversation_id=conversation_id,
                    role="user",
                    content=user_text,
                    audio_transcribed=is_audio
                )
                db.add(user_msg)
                db.commit()

                # Acknowledge user input to client
                await websocket.send_json({
                    "type": "user_acknowledged",
                    "content": user_text,
                    "is_audio": is_audio
                })

                # Retrieve history for context
                past_messages = db.query(Message).filter(
                    Message.conversation_id == conversation_id
                ).order_by(Message.created_at.asc()).all()

                formatted_history = [
                    {"role": m.role, "content": m.content}
                    for m in past_messages
                ]

                # Stream orchestrator steps
                collected_chunks = []
                async for event in orchestrator.generate_response(formatted_history):
                    await websocket.send_json(event)
                    if event.get("type") == "agent_chunk":
                        collected_chunks.append(event.get("content", ""))

                full_reply = "".join(collected_chunks)
                if full_reply:
                    # Save assistant message to database
                    asst_msg = Message(
                        conversation_id=conversation_id,
                        role="assistant",
                        content=full_reply
                    )
                    db.add(asst_msg)
                    db.commit()

            elif event_type == "client_state":
                # Tracks client-side mic state, errors, or audio playback completion
                pass

    except WebSocketDisconnect:
        logger.info(f"WebSocket client disconnected: {conversation_id}")
    except Exception as e:
        logger.error(f"WebSocket error in {conversation_id}: {str(e)}")
        try:
            await websocket.send_json({"type": "error", "message": f"Server error: {str(e)}"})
        except Exception:
            pass
