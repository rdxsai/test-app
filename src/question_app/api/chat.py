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
from ..services.tutor.azure_client import AzureAPIMClient
from ..services.wcag_mcp_client import WCAGMCPClient
from ..services.student_service import StudentService
from ..services.general_chat_service import GeneralChatService
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
        "instance_a_deployment_name": config.AZURE_OPENAI_INSTANCE_A_DEPLOYMENT_ID,
        "tutor_deployment_name": config.AZURE_OPENAI_TUTOR_DEPLOYMENT_ID,
        "reasoning_deployment_name": config.AZURE_OPENAI_REASONING_DEPLOYMENT_ID,
        "api_version": config.AZURE_OPENAI_API_VERSION
    }

    # Create Azure client for WCAG MCP function calling
    azure_client = AzureAPIMClient(
        endpoint=azure_config["endpoint"],
        deployment=(
            azure_config.get("reasoning_deployment_name")
            or azure_config["deployment_name"]
        ),
        api_key=azure_config["api_key"],
        api_version=azure_config.get("api_version", "2024-02-15-preview"),
    )

    wcag_mcp = WCAGMCPClient(
        command=config.WCAG_MCP_COMMAND,
        azure_client=azure_client,
    ) if config.WCAG_MCP_ENABLED else None
    if wcag_mcp:
        logger.info("Chat API: WCAG MCP client created with LLM-driven tool calling.")

    general_chat_service = GeneralChatService(
        azure_config=azure_config,
        vector_store_service=vector_service,
        wcag_mcp_client=wcag_mcp,
        db_manager=vector_service.db,
    )
    logger.info("Chat API: GeneralChatService initialized successfully.")

    student_service = StudentService() if config.STUDENT_MCP_ENABLED else None
    if student_service:
        logger.info("Chat API: StudentService initialized (direct DB access).")

    guided_tutor_system = HybridCrewAISocraticSystem(
        azure_config=azure_config,
        vector_store_service=vector_service,
        wcag_mcp_client=wcag_mcp,
        student_mcp_client=student_service,
    )
    logger.info("Chat API: HybridCrewAISocraticSystem initialized successfully.")

except ValueError as e:
    logger.critical(f"Failed to initialize vector store: {e}")
    general_chat_service = None
    guided_tutor_system = None
except Exception as e:
    logger.critical(f"Failed to initialize chat services: {e}", exc_info=True)
    general_chat_service = None
    guided_tutor_system = None
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

# --- Constants for instance A session bootstrap ---
DEFAULT_CHAT_SESSION_ID = "default-student"

@router.post("/message")
async def handle_chat_message(chat_message : ChatMessage):
    """
    Handles a single chat message via POST request.
    (This is the updated, corrected version)
    """
    
    if not general_chat_service:
        logger.error("General chat service is not initialized. Check server logs.")
        raise HTTPException(status_code=503, detail="Chat service is offline. Please check server logs.")

    try:
        session = await general_chat_service.ensure_session(
            chat_message.student_id or DEFAULT_CHAT_SESSION_ID
        )

        if chat_message.message == "START_SESSION":
            logger.info(
                "Handling new conversation start for session_id: %s",
                session["session_id"],
            )
            session = await general_chat_service.start_new_session(session["session_id"])
            welcome_message = load_welcome_message()
            return {
                "response": welcome_message,
                "student_id": session["session_id"],
                "session_metadata": {
                    "session_number": session["session_number"],
                    "intent_executed": "start_session",
                    "analysis": {},
                    "progress": {},
                }
            }

        logger.info(f"Received chat message for session_id: {session['session_id']}")
        result = await general_chat_service.handle_message(
            session_id=session["session_id"],
            user_message=chat_message.message,
        )

        return {
            "response": result.get("response"),
            "student_id": result.get("session_id"),
            "session_metadata": result.get("session_metadata"),
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

    if not general_chat_service:
        await websocket.send_json({"type": "error", "message": "Chat service is offline."})
        await websocket.close(code=1011)
        return

    await websocket.send_json({"type": "connected"})

    session_id = None

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
                session = await general_chat_service.ensure_session(
                    msg.get("student_id") or DEFAULT_CHAT_SESSION_ID
                )
                session_id = session["session_id"]
                await websocket.send_json({
                    "type": "authenticated",
                    "student_id": session["session_id"],
                    "session_number": session["session_number"],
                })

            # --- NEW SESSION ---
            elif msg_type == "new_session":
                session = await general_chat_service.ensure_session(
                    session_id or DEFAULT_CHAT_SESSION_ID
                )
                session_id = session["session_id"]
                session = await general_chat_service.start_new_session(session_id)

                welcome = load_welcome_message()
                await websocket.send_json({
                    "type": "welcome",
                    "content": welcome,
                    "student_id": session["session_id"],
                    "session_number": session["session_number"],
                })

            # --- CHAT MESSAGE ---
            elif msg_type == "message":
                content = msg.get("content", "").strip()
                if not content:
                    await websocket.send_json({"type": "error", "message": "Empty message"})
                    continue

                session = await general_chat_service.ensure_session(
                    session_id or DEFAULT_CHAT_SESSION_ID
                )
                session_id = session["session_id"]
                await general_chat_service.handle_message_streaming(
                    session_id=session_id,
                    user_message=content,
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
        logger.info(f"WS: Client disconnected (session_id={session_id})")
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

    if not guided_tutor_system:
        await websocket.send_json({"type": "error", "message": "Tutor system is offline."})
        await websocket.close(code=1011)
        return

    if not guided_tutor_system.student_mcp:
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
                profile = await guided_tutor_system.student_mcp.get_profile(student_id)
                session = await guided_tutor_system.student_mcp.get_active_session(student_id) if profile else None

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
                    await guided_tutor_system.student_mcp.update_session_state(
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
                    history = guided_tutor_system.get_conversation_history(student_id)
                    assistant_turns = sum(1 for m in history if m.get("role") == "assistant")

                    if assistant_turns == 0:
                        # Brand new — send welcome + first question
                        await websocket.send_json({
                            "type": "welcome",
                            "content": "Welcome! I'm your web accessibility tutor. Let me learn a bit about you so I can personalize your learning.",
                            "student_id": student_id,
                            "stage": "onboarding",
                        })
                        first_question = guided_tutor_system._ONBOARDING_QUESTIONS[0]
                        await websocket.send_json({
                            "type": "onboarding_question",
                            "step": 1,
                            "total_steps": 3,
                            **first_question,
                        })
                        guided_tutor_system.append_to_conversation(
                            student_id, "assistant", guided_tutor_system._ONBOARDING_PROMPTS[0]
                        )
                    else:
                        # Returning mid-onboarding — send the next unanswered question
                        next_step = min(assistant_turns, 2)
                        question = guided_tutor_system._ONBOARDING_QUESTIONS[next_step]
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

                await guided_tutor_system.conduct_guided_session_streaming(
                    student_id=student_id,
                    student_response=content,
                    session_id=session_id,
                    ws_send=ws_send,
                )

            # --- RESET SESSION ---
            elif msg_type == "reset_session":
                if student_id:
                    # Clear conversation memory for this student
                    guided_tutor_system.conversation_memory.pop(student_id, None)
                    guided_tutor_system._save_conversation_memory()
                    # Invalidate session cache
                    if session_id:
                        guided_tutor_system._session_cache.invalidate(session_id)
                        if (
                            guided_tutor_system.student_mcp
                            and hasattr(guided_tutor_system.student_mcp, "clear_session_runtime_cache")
                        ):
                            await guided_tutor_system.student_mcp.clear_session_runtime_cache(
                                session_id
                            )
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
        if student_id and session_id and guided_tutor_system.student_mcp:
            try:
                await guided_tutor_system.student_mcp.save_session_summary(
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
