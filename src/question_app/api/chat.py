"""
Chat API module for the Question App.
WebSocket streaming + POST fallback.
"""

import asyncio
import json
import logging
from typing import Dict

from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from ..core import config, get_logger
from ..utils import (
    get_default_chat_system_prompt,
    get_default_welcome_message,
    load_chat_system_prompt,
    load_welcome_message,       # <-- We will use this
    save_chat_system_prompt,
    save_welcome_message,
)
from ..services.tutor.hybrid_system import HybridCrewAISocraticSystem
from ..services.tutor.simple_system import AzureAPIMClient
from ..services.wcag_mcp_client import WCAGMCPClient
from ..services.student_mcp_client import StudentMCPClient
from ..api.pg_vector_store import VectorStoreService


logger = get_logger(__name__)

# Create router for chat endpoints
router = APIRouter(prefix="/chat", tags=["chat"])

# Templates setup
templates = Jinja2Templates(directory="templates")

# --- === INITIALIZATION === ---
try:
    vector_service = VectorStoreService()

    azure_config = {
        "api_key": config.AZURE_OPENAI_SUBSCRIPTION_KEY,
        "endpoint": config.AZURE_OPENAI_ENDPOINT,
        "deployment_name": config.AZURE_OPENAI_DEPLOYMENT_ID,
        "api_version": config.AZURE_OPENAI_API_VERSION
    }

    # Create Azure client for WCAG MCP function calling
    azure_client = AzureAPIMClient(
        endpoint=azure_config["endpoint"],
        deployment=azure_config["deployment_name"],
        api_key=azure_config["api_key"],
        api_version=azure_config.get("api_version", "2024-02-15-preview"),
    )

    wcag_mcp = WCAGMCPClient(
        command=config.WCAG_MCP_COMMAND,
        azure_client=azure_client,
    ) if config.WCAG_MCP_ENABLED else None
    if wcag_mcp:
        logger.info("Chat API: WCAG MCP client created with LLM-driven tool calling.")

    import sys
    student_mcp = StudentMCPClient(
        command=sys.executable,
        args=["-m", "student_mcp"],
    ) if config.STUDENT_MCP_ENABLED else None
    if student_mcp:
        logger.info("Chat API: Student MCP client created for programmatic state management.")

    tutor_system = HybridCrewAISocraticSystem(
        azure_config=azure_config,
        vector_store_service=vector_service,
        wcag_mcp_client=wcag_mcp,
        student_mcp_client=student_mcp,
    )
    logger.info("Chat API: HybridCrewAISocraticSystem initialized successfully.")

except ValueError as e:
    logger.critical(f"Failed to initialize vector store: {e}")
    tutor_system = None
except Exception as e:
    logger.critical(f"Failed to initialize HybridCrewAISocraticSystem: {e}", exc_info=True)
    tutor_system = None
# --- === END OF INITIALIZATION === ---


# Chat endpoints
@router.get("/", response_class=HTMLResponse)
async def chat_page(request: Request):
    """Chat assistant page"""
    return templates.TemplateResponse("chat.html", {"request": request})


#Define a pydantic model for incoming request body
class ChatMessage(BaseModel):
    message : str
    student_id: str | None = None 

# --- Constants for our new default student ---
DEFAULT_STUDENT_ID = "default-student"
DEFAULT_STUDENT_NAME = "Default Student"
DEFAULT_TOPIC = "Web Accessibility"

@router.post("/message")
async def handle_chat_message(chat_message : ChatMessage):
    """
    Handles a single chat message via POST request.
    (This is the updated, corrected version)
    """
    
    if not tutor_system:
        logger.error("Tutor system is not initialized. Check server logs.")
        raise HTTPException(status_code=503, detail="Tutor system is offline. Please check server logs.")

    try:
        # --- (Default student logic is correct) ---
        student_id = chat_message.student_id or DEFAULT_STUDENT_ID
        
        profile = tutor_system.get_student_profile(student_id)
        if not profile:
            logger.warning(f"Student profile '{student_id}' not found. Creating a default profile.")
            try:
                tutor_system.create_student_profile(
                    name=DEFAULT_STUDENT_NAME,
                    topic=DEFAULT_TOPIC,
                    student_id_override=student_id 
                )
                # After creating, we must load the profile again to use it
                profile = tutor_system.get_student_profile(student_id)
                if not profile: # Still not found? Something is wrong.
                    raise Exception("Failed to create or load default student profile.")
            except Exception as create_e:
                logger.error(f"Failed to create default student profile: {create_e}", exc_info=True)
                raise HTTPException(status_code=500, detail="Failed to create student profile.")
        # --- (End of default student logic) ---

        
        # --- === THIS IS THE NEW FIX === ---
        # If the message is "START_SESSION", just send the welcome message.
        if chat_message.message == "START_SESSION":
            logger.info(f"Handling new conversation start for student_id: {student_id}")
            welcome_message = load_welcome_message() # Use the existing utility
            
            # We increment the session count
            if profile:
                profile.total_sessions += 1
                tutor_system.db.save_student_profile(profile)
                
            return {
                "response": welcome_message,
                "student_id": student_id,
                "session_metadata": {
                    "session_number": profile.total_sessions if profile else 1,
                    "intent_executed": "start_session",
                    "analysis": {}, "progress": {} # Send empty metadata
                }
            }
        # --- === END OF NEW FIX === ---

        
        # If the message is not "START_SESSION", proceed with the normal AI workflow
        logger.info(f"Received chat message for student_id: {student_id}")
        
        result = await tutor_system.conduct_socratic_session(
            student_id=student_id,
            student_response=chat_message.message
        )

        if result.get("status") == "error":
            raise HTTPException(status_code=500 , detail = result.get("error" , "An unknown error occured in tutoring session"))
        
        return {
            "response" : result.get("tutor_response"),
            "student_id": student_id, 
            "session_metadata" : result.get("session_metadata")
        }
    except HTTPException as e:
        logger.error(f"HTTP Exception in handle_chat_message : {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error in handle_chat_message : {e}" , exc_info=True)
        raise HTTPException(
            status_code=500 , detail = f"Failed to process chat message : {str(e)}"
        )

# ============================================================================
# WEBSOCKET ENDPOINT
# ============================================================================

@router.websocket("/ws")
async def websocket_chat(websocket: WebSocket):
    """
    WebSocket endpoint for real-time chat with stage updates and token streaming.

    Protocol:
    Client -> Server:
      {"type": "auth", "student_id": "default-student"}
      {"type": "message", "content": "what is alt text?"}
      {"type": "new_session"}
      {"type": "ping"}

    Server -> Client:
      {"type": "connected"}
      {"type": "authenticated", "student_id": "...", "session_number": N}
      {"type": "stage", "stage": "classifying|searching|analyzing|assessing|composing"}
      {"type": "stream_start"}
      {"type": "token", "content": "..."}
      {"type": "stream_end", "metadata": {...}}
      {"type": "welcome", "content": "...", "student_id": "..."}
      {"type": "error", "message": "..."}
      {"type": "pong"}
    """
    await websocket.accept()

    if not tutor_system:
        await websocket.send_json({"type": "error", "message": "Tutor system is offline."})
        await websocket.close(code=1011)
        return

    await websocket.send_json({"type": "connected"})

    student_id = None

    async def ws_send(data: dict):
        """Helper to send JSON over WebSocket."""
        await websocket.send_json(data)

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "message": "Invalid JSON"})
                continue

            msg_type = msg.get("type")

            # --- AUTH ---
            if msg_type == "auth":
                student_id = msg.get("student_id") or DEFAULT_STUDENT_ID
                profile = await asyncio.to_thread(
                    tutor_system.get_student_profile, student_id
                )
                if not profile:
                    try:
                        await asyncio.to_thread(
                            tutor_system.create_student_profile,
                            DEFAULT_STUDENT_NAME,
                            DEFAULT_TOPIC,
                            "",
                            student_id,
                        )
                        profile = await asyncio.to_thread(
                            tutor_system.get_student_profile, student_id
                        )
                    except Exception as e:
                        logger.error(f"WS: Failed to create student: {e}", exc_info=True)
                        await websocket.send_json({
                            "type": "error",
                            "message": "Failed to create student profile."
                        })
                        continue

                session_number = profile.total_sessions if profile else 0
                await websocket.send_json({
                    "type": "authenticated",
                    "student_id": student_id,
                    "session_number": session_number,
                })

            # --- NEW SESSION ---
            elif msg_type == "new_session":
                if not student_id:
                    student_id = DEFAULT_STUDENT_ID

                profile = await asyncio.to_thread(
                    tutor_system.get_student_profile, student_id
                )
                if profile:
                    profile.total_sessions += 1
                    await asyncio.to_thread(tutor_system.db.save_student_profile, profile)

                welcome = load_welcome_message()
                await websocket.send_json({
                    "type": "welcome",
                    "content": welcome,
                    "student_id": student_id,
                    "session_number": profile.total_sessions if profile else 1,
                })

            # --- CHAT MESSAGE ---
            elif msg_type == "message":
                content = msg.get("content", "").strip()
                if not content:
                    await websocket.send_json({"type": "error", "message": "Empty message"})
                    continue

                if not student_id:
                    student_id = DEFAULT_STUDENT_ID

                await tutor_system.conduct_socratic_session_streaming(
                    student_id=student_id,
                    student_response=content,
                    ws_send=ws_send,
                )

            # --- PING / KEEPALIVE ---
            elif msg_type == "ping":
                await websocket.send_json({"type": "pong"})

            else:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Unknown message type: {msg_type}"
                })

    except WebSocketDisconnect:
        logger.info(f"WS: Client disconnected (student_id={student_id})")
    except Exception as e:
        logger.error(f"WS: Unexpected error: {e}", exc_info=True)
        try:
            await websocket.send_json({"type": "error", "message": "Internal server error"})
            await websocket.close(code=1011)
        except Exception:
            pass


# ============================================================================
# INSTANCE B: GUIDED LEARNING
# ============================================================================

@router.get("/guided", response_class=HTMLResponse)
async def guided_chat_page(request: Request):
    """Instance B — Guided learning chat page."""
    return templates.TemplateResponse("chat_guided.html", {"request": request})


@router.websocket("/guided/ws")
async def websocket_guided_chat(websocket: WebSocket):
    """
    Instance B WebSocket — guided learning with stage-based Socratic tutoring.

    Protocol (Client → Server):
      {"type": "auth", "student_id": "..."}
      {"type": "message", "content": "..."}
      {"type": "ping"}

    Protocol (Server → Client — includes Instance A types plus):
      {"type": "stage_update", "stage": "...", "objective": "...", "summary": "..."}
      {"type": "mastery_update", "objective_id": "...", "new_level": "..."}
      {"type": "assessment_score", "asked": N, "correct": M, "total": T, "passed": bool|null}
      {"type": "onboarding_complete", "profile": {...}, "first_objective": "..."}
    """
    await websocket.accept()

    if not tutor_system:
        await websocket.send_json({"type": "error", "message": "Tutor system is offline."})
        await websocket.close(code=1011)
        return

    if not tutor_system.student_mcp:
        await websocket.send_json({"type": "error", "message": "Student MCP not available."})
        await websocket.close(code=1011)
        return

    await websocket.send_json({"type": "connected", "instance": "guided"})

    student_id = None
    session_id = None

    async def ws_send(data: dict):
        await websocket.send_json(data)

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "message": "Invalid JSON"})
                continue

            msg_type = msg.get("type")

            # --- AUTH ---
            if msg_type == "auth":
                student_id = msg.get("student_id", "").strip()
                if not student_id:
                    await websocket.send_json({"type": "error", "message": "student_id required"})
                    continue

                # Generate a session ID for this connection
                import uuid
                session_id = f"guided-{uuid.uuid4().hex[:12]}"

                # Check if student has a profile in the Student MCP
                profile = await tutor_system.student_mcp.get_profile(student_id)
                session = await tutor_system.student_mcp.get_active_session(student_id) if profile else None

                if profile:
                    # Returning student — resume or start new objective
                    current_stage = (session or {}).get("current_stage", "introduction")
                    objective = (session or {}).get("active_objective_id", "")
                    await websocket.send_json({
                        "type": "authenticated",
                        "student_id": student_id,
                        "instance": "guided",
                        "stage": current_stage,
                        "objective": objective,
                        "has_profile": True,
                    })

                    # Create a new session for this connection
                    await tutor_system.student_mcp.update_session_state(
                        session_id, student_id=student_id,
                        stage=current_stage, active_objective_id=objective,
                    )
                else:
                    # New student — onboarding handled by conduct_guided_session_streaming.
                    # Don't create a session here (no profile yet → FK would fail).
                    # Send auth confirmation, then the first onboarding prompt.
                    await websocket.send_json({
                        "type": "authenticated",
                        "student_id": student_id,
                        "instance": "guided",
                        "stage": "onboarding",
                        "has_profile": False,
                    })

                    # Check if this student has partial onboarding progress
                    history = tutor_system.get_conversation_history(student_id)
                    assistant_turns = sum(1 for m in history if m.get("role") == "assistant")

                    if assistant_turns == 0:
                        # Brand new — send welcome + first question
                        await websocket.send_json({
                            "type": "welcome",
                            "content": "Welcome! I'm your web accessibility tutor. Let me learn a bit about you so I can personalize your learning.",
                            "student_id": student_id,
                            "stage": "onboarding",
                        })
                        first_question = tutor_system._ONBOARDING_QUESTIONS[0]
                        await websocket.send_json({
                            "type": "onboarding_question",
                            "step": 1,
                            "total_steps": 3,
                            **first_question,
                        })
                        tutor_system.append_to_conversation(
                            student_id, "assistant", tutor_system._ONBOARDING_PROMPTS[0]
                        )
                    else:
                        # Returning mid-onboarding — send the next unanswered question
                        next_step = min(assistant_turns, 2)
                        question = tutor_system._ONBOARDING_QUESTIONS[next_step]
                        await websocket.send_json({
                            "type": "welcome",
                            "content": "Welcome back! Let's continue where we left off.",
                            "student_id": student_id,
                            "stage": "onboarding",
                        })
                        await websocket.send_json({
                            "type": "onboarding_question",
                            "step": next_step + 1,
                            "total_steps": 3,
                            **question,
                        })

            # --- CHAT MESSAGE ---
            elif msg_type == "message":
                content = msg.get("content", "").strip()
                if not content:
                    await websocket.send_json({"type": "error", "message": "Empty message"})
                    continue

                if not student_id or not session_id:
                    await websocket.send_json({"type": "error", "message": "Not authenticated"})
                    continue

                await tutor_system.conduct_guided_session_streaming(
                    student_id=student_id,
                    student_response=content,
                    session_id=session_id,
                    ws_send=ws_send,
                )

            # --- RESET SESSION ---
            elif msg_type == "reset_session":
                if student_id:
                    # Clear conversation memory for this student
                    tutor_system.conversation_memory.pop(student_id, None)
                    tutor_system._save_conversation_memory()
                    # Invalidate session cache
                    if session_id:
                        tutor_system._session_cache.invalidate(session_id)
                    logger.info(f"WS Guided: Session reset for {student_id}")
                    await websocket.send_json({"type": "session_reset", "student_id": student_id})

            # --- PING ---
            elif msg_type == "ping":
                await websocket.send_json({"type": "pong"})

            else:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Unknown message type: {msg_type}"
                })

    except WebSocketDisconnect:
        logger.info(f"WS Guided: Client disconnected (student_id={student_id})")
        # Save session summary on disconnect
        if student_id and session_id and tutor_system.student_mcp:
            try:
                await tutor_system.student_mcp.save_session_summary(
                    session_id, student_id, "short",
                    content=json.dumps({"disconnected": True}),
                )
            except Exception:
                pass
    except Exception as e:
        logger.error(f"WS Guided: Unexpected error: {e}", exc_info=True)
        try:
            await websocket.send_json({"type": "error", "message": "Internal server error"})
            await websocket.close(code=1011)
        except Exception:
            pass


@router.get("/system-prompt", response_class=HTMLResponse)
async def chat_system_prompt_page(request: Request):
    """Chat system prompt edit page"""
    current_prompt = load_chat_system_prompt()
    default_prompt = get_default_chat_system_prompt()

    return templates.TemplateResponse(
        "chat_system_prompt_edit.html",
        {
            "request": request,
            "current_prompt": current_prompt,
            "default_prompt": default_prompt,
        },
    )


@router.post("/system-prompt")
async def save_chat_system_prompt_endpoint(request: Request):
    """Save chat system prompt"""
    try:
        form = await request.form()
        prompt_value = form.get("prompt", "")
        prompt = prompt_value.strip() if isinstance(prompt_value, str) else ""

        if not prompt:
            raise HTTPException(status_code=400, detail="System prompt cannot be empty")

        if save_chat_system_prompt(prompt):
            logger.info("Chat system prompt saved successfully")
            return {"success": True, "message": "Chat system prompt saved successfully"}
        else:
            raise HTTPException(
                status_code=500, detail="Failed to save chat system prompt"
            )

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error saving chat system prompt: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/system-prompt/default")
async def get_default_chat_system_prompt_endpoint():
    """Get default chat system prompt"""
    return {"default_prompt": get_default_chat_system_prompt()}


@router.get("/welcome-message")
async def get_chat_welcome_message():
    """Get the current chat welcome message"""
    try:
        welcome_message = load_welcome_message()
        return {"welcome_message": welcome_message}
    except Exception as e:
        logger.error(f"Error loading welcome message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/welcome-message")
async def save_chat_welcome_message(request: Request):
    """Save chat welcome message"""
    try:
        content_type = request.headers.get("content-type", "")

        if "application/json" in content_type:
            body = await request.json()
            message = body.get("welcome_message", "").strip()
        else:
            form = await request.form()
            message_value = form.get("welcome_message", "")
            message = message_value.strip() if isinstance(message_value, str) else ""

        if not message:
            raise HTTPException(
                status_code=400, detail="Welcome message cannot be empty"
            )

        if save_welcome_message(message):
            logger.info("Welcome message saved successfully")
            return {"success": True, "message": "Welcome message saved successfully"}
        else:
            raise HTTPException(
                status_code=500, detail="Failed to save welcome message"
            )

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error saving welcome message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/welcome-message/default")
async def get_default_chat_welcome_message():
    """Get default chat welcome message"""
    try:
        default_message = get_default_welcome_message()
        return {"default_welcome_message": default_message}
    except Exception as e:
        logger.error(f"Error loading default welcome message: {e}")
        raise HTTPException(status_code=500, detail=str(e))