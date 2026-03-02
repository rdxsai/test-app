"""
API endpoints for managing questions.
--- THIS IS THE FULLY CORRECTED VERSION ---
- Fixes the 'generate-feedback' TypeError
- Includes the 'suggest-objectives' endpoint
- FIX: Adds Markdown-to-HTML conversion for the preview
"""
import logging
import json

from fastapi import APIRouter, HTTPException, Request, Depends, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
import httpx
import markdown


from ..core import config, get_logger
from ..services.database import get_database_manager
from ..models import QuestionUpdate
from ..services.ai_service import AIGeneratorService
from ..models import QuestionUpdate, NewQuestion

logger = get_logger(__name__)
router = APIRouter(prefix="/questions", tags=["questions"])
templates = Jinja2Templates(directory="templates")

# Initialize services
db = get_database_manager()
ai_generator = AIGeneratorService()


def format_sse_event(event_type: str, data: dict) -> str:
    """Format a dict as a Server-Sent Event string."""
    return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"


@router.get("/new", response_class=HTMLResponse)
async def new_question_page(request: Request):
    """
    Serves the page for creating a new question.
    """
    logger.info("Loading new question creation page")
    try:
        all_objectives = db.list_all_objectives()
        
        # Create an empty question structure
        empty_question = {
            'id': 'new',  # Special marker for new questions
            'question_text': '',
            'question_text_html': '',
            'objective_ids': [],
            'answers': [
                {'id': 'new_1', 'text': '', 'text_html': '', 'is_correct': False, 'feedback_text': '', 'feedback_approved': False},
                {'id': 'new_2', 'text': '', 'text_html': '', 'is_correct': False, 'feedback_text': '', 'feedback_approved': False},
                {'id': 'new_3', 'text': '', 'text_html': '', 'is_correct': False, 'feedback_text': '', 'feedback_approved': False},
                {'id': 'new_4', 'text': '', 'text_html': '', 'is_correct': False, 'feedback_text': '', 'feedback_approved': False},
            ]
        }
        
        return templates.TemplateResponse(
            "edit_question.html",
            {
                "request": request,
                "question": empty_question,
                "all_objectives": all_objectives,
                "is_new": True  # Flag to tell template this is a new question
            },
        )
    except Exception as e:
        logger.error(f"Error loading new question page: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not load new question page.")


@router.post("/", response_class=JSONResponse)
async def create_question(data: NewQuestion):
    """
    Creates a new question in the database.
    Validates that question_text and at least one answer are provided.
    """
    logger.info("Creating new question")
    
    # Validation
    if not data.question_text or not data.question_text.strip():
        raise HTTPException(status_code=400, detail="Question text is required")
    
    if not data.answers or len(data.answers) == 0:
        raise HTTPException(status_code=400, detail="At least one answer is required")
    
    # Check if any answer text is provided
    if not any(answer.text.strip() for answer in data.answers):
        raise HTTPException(status_code=400, detail="At least one answer must have text")
    
    try:
        new_question_id = db.create_question_with_answers(data)

        # Auto-generate embeddings for the new question
        try:
            from .pg_vector_store import VectorStoreService
            vector_service = VectorStoreService()
            chunks = await vector_service.embed_single_question(new_question_id)
            logger.info(f"Auto-embedded {chunks} chunks for new question {new_question_id}")
        except Exception as embed_err:
            logger.warning(f"Embedding generation failed for new question {new_question_id}: {embed_err}")

        logger.info(f"Successfully created question {new_question_id}")
        return {
            "success": True,
            "message": "Question created successfully",
            "question_id": new_question_id
        }

    except Exception as e:
        logger.error(f"Error creating question: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create question")

@router.get("/{question_id}", response_class=HTMLResponse)
async def edit_question_page(request: Request, question_id: str):
    """
    Serves the edit page for a single question.
    """
    logger.info(f"Loading edit page for question_id: {question_id}")
    try:
        question_data = db.load_question_details(question_id)
        if not question_data:
            raise HTTPException(status_code=404, detail="Question not found")
        
        all_objectives = db.list_all_objectives()
        
        # Get associated objectives with full text
        associated_objectives = []
        if question_data.get('objective_ids'):
            all_objectives_dict = {obj['id']: obj for obj in all_objectives}
            for obj_id in question_data['objective_ids']:
                if obj_id in all_objectives_dict:
                    associated_objectives.append(all_objectives_dict[obj_id])
        
        # --- === 2. THIS IS THE FIX FOR THE BLANK PREVIEW === ---
        # The template 'edit_question.html' (your original one)
        # expects HTML-converted text. We must do that conversion here.
        
        import re
        md = markdown.Markdown(extensions=['fenced_code', 'codehilite'])
        SAFE_TAGS = {'p', 'br', 'strong', 'b', 'em', 'i', 'code', 'pre', 'span',
                     'ul', 'ol', 'li', 'a', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
                     'blockquote', 'hr', 'div', 'table', 'thead', 'tbody', 'tr',
                     'th', 'td', 'img', 'del', 's', 'sub', 'sup'}

        def sanitize_html(html_str):
            def replace_tag(m):
                tag_name = m.group(1).strip().split()[0].lower().lstrip('/')
                if tag_name in SAFE_TAGS:
                    return m.group(0)
                return m.group(0).replace('<', '&lt;').replace('>', '&gt;')
            return re.sub(r'<(/?\s*[a-zA-Z][^>]*)>', replace_tag, html_str)

        # 1. Convert the main question text
        if question_data.get('question_text'):
            question_data['question_text_html'] = sanitize_html(md.convert(question_data['question_text']))
            md.reset()
        else:
            question_data['question_text_html'] = ''

        # 2. Convert the text for each answer
        for answer in question_data.get('answers', []):
            if answer.get('text'):
                answer['text_html'] = sanitize_html(md.convert(answer['text']))
                md.reset()
            else:
                answer['text_html'] = ''
        # --- === END OF FIX === ---
        
        return templates.TemplateResponse(
            "edit_question.html",
            {
                "request": request,
                "question": question_data,  # <-- This dict now has the _html fields
                "all_objectives": all_objectives,
                "associated_objectives": associated_objectives,
            },
        )
    except Exception as e:
        logger.error(f"Error loading edit page: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not load edit page.")


@router.put("/{question_id}", response_class=JSONResponse)
async def save_question(question_id: str, data: QuestionUpdate, background_tasks: BackgroundTasks):
    """
    Saves updates to a question (auto-save).
    (This is the correct, working version)
    """
    try:
        success = db.update_question_and_answers(question_id, data)
        if not success:
            raise HTTPException(status_code=404, detail="Question not found")

        # Regenerate embeddings for the edited question
        try:
            from .pg_vector_store import VectorStoreService
            vector_service = VectorStoreService()
            chunks = await vector_service.embed_single_question(question_id)
            logger.info(f"Re-embedded {chunks} chunks for edited question {question_id}")
        except Exception as embed_err:
            logger.warning(f"Embedding regeneration failed for question {question_id}: {embed_err}")

        return {"success": True, "message": "Question updated successfully"}
    except Exception as e:
        logger.error(f"Error saving question {question_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to save question.")


@router.delete("/{question_id}", response_class=JSONResponse)
async def delete_question(question_id: str):
    """
    Deletes a question from the database.
    (This is the correct, working version)
    """
    try:
        success = db.delete_question(question_id)
        if not success:
            raise HTTPException(status_code=404, detail="Question not found")
        return {"success": True, "message": "Question deleted."}
    except Exception as e:
        logger.error(f"Error deleting question {question_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to delete question.")


@router.post("/{question_id}/generate-feedback", response_class=JSONResponse)
async def generate_feedback_for_all_unapproved(question_id: str):
    """
    Generates AI feedback for all unapproved answers for a given question.
    (This is the correct, working version)
    """
    logger.info(f"Generating feedback request started for question {question_id}")
    
    try:
        question = db.load_question_details(question_id)
        if not question:
            raise HTTPException(status_code=404, detail="Question not found")
        
        updated_answers = []
        for answer in question.get("answers", []):
            if not answer.get("feedback_approved", False):
                logger.info(f"Generating feedback for unapproved answer_id: {answer['id']}")
                
                feedback_text = await ai_generator.generate_feedback_for_answer(
                    question_text=question['question_text'],
                    answer_text=answer['text'],
                    is_correct=answer['is_correct']
                )
                
                db.update_answer_feedback(answer['id'], feedback_text)
                updated_answers.append({
                    "answer_id": answer['id'],
                    "feedback_text": feedback_text
                })
        
        return {"success": True, "message": "Feedback generated.", "updated_answers": updated_answers}
    
    except httpx.HTTPStatusError as e:
        error_message = f"AI Service Error: {e}"
        if e.response.status_code == 429:
            error_message = "AI Service Error: Too many requests. Please wait and try again."
        elif e.response:
            try:
                error_detail = e.response.json()
                error_message = f"AI Error: {error_detail.get('error', {}).get('message', e)}"
            except Exception:
                pass 
        logger.error(f"Error in generate_feedback: {error_message}", exc_info=True)
        raise HTTPException(status_code=500, detail=error_message)
    
    except Exception as e:
        logger.error(f"Error in generate_feedback: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{question_id}/generate-feedback-stream")
async def generate_feedback_stream(question_id: str):
    """
    SSE endpoint that streams real-time progress while generating AI feedback
    for all unapproved answers.
    """
    async def event_generator():
        try:
            question = db.load_question_details(question_id)
            if not question:
                yield format_sse_event("fatal_error", {"message": "Question not found"})
                return

            unapproved = [a for a in question.get("answers", []) if not a.get("feedback_approved", False)]
            total = len(unapproved)

            if total == 0:
                yield format_sse_event("all_done", {
                    "message": "No unapproved answers to process",
                    "total": 0,
                    "processed": 0,
                })
                return

            yield format_sse_event("stream_start", {
                "total": total,
                "question_id": question_id,
            })

            processed = 0
            for idx, answer in enumerate(unapproved, start=1):
                answer_preview = (answer.get("text") or "")[:80]
                yield format_sse_event("answer_start", {
                    "answer_id": answer["id"],
                    "answer_text_preview": answer_preview,
                    "is_correct": answer.get("is_correct", False),
                    "index": idx,
                    "total": total,
                })

                try:
                    feedback_text = await ai_generator.generate_feedback_for_answer(
                        question_text=question["question_text"],
                        answer_text=answer["text"],
                        is_correct=answer["is_correct"],
                    )
                    db.update_answer_feedback(answer["id"], feedback_text)
                    processed += 1

                    yield format_sse_event("answer_complete", {
                        "answer_id": answer["id"],
                        "feedback_text": feedback_text,
                        "index": idx,
                        "total": total,
                    })
                except Exception as e:
                    logger.error(f"Error generating feedback for answer {answer['id']}: {e}", exc_info=True)
                    yield format_sse_event("answer_error", {
                        "answer_id": answer["id"],
                        "error": str(e),
                        "index": idx,
                        "total": total,
                    })

            yield format_sse_event("all_done", {
                "message": "All feedback generated successfully",
                "total": total,
                "processed": processed,
            })

        except Exception as e:
            logger.error(f"Fatal error in feedback stream: {e}", exc_info=True)
            yield format_sse_event("fatal_error", {"message": str(e)})

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/{question_id}/suggest-objectives", response_class=JSONResponse)
async def suggest_objectives(question_id: str):
    """
    (Req 8.2) Suggests existing objectives for a question using AI.
    (This is the correct, working version)
    """
    try:
        question = db.load_question_details(question_id)
        if not question:
            raise HTTPException(status_code=404, detail="Question not found")
        
        suggestions = await ai_generator.suggest_objectives_for_question(
            question['question_text']
        )
        
        return {"suggestions": suggestions}
    except Exception as e:
        logger.error(f"Error suggesting objectives: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to suggest objectives.")


@router.get("/{question_id}/suggest-objectives-stream")
async def suggest_objectives_stream(question_id: str):
    """
    SSE endpoint that streams real-time progress while ranking objectives
    for a question using LLM.
    """
    async def event_generator():
        try:
            # Phase 1: Load question
            yield format_sse_event("phase", {
                "stage": "loading_question",
                "message": "Loading question...",
                "percent": 10,
            })

            question = db.load_question_details(question_id)
            if not question:
                yield format_sse_event("fatal_error", {"message": "Question not found"})
                return

            # Phase 2: Load objectives
            yield format_sse_event("phase", {
                "stage": "loading_objectives",
                "message": "Loading objectives from database...",
                "percent": 25,
            })

            all_objectives = db.list_all_objectives()
            if not all_objectives:
                yield format_sse_event("all_done", {
                    "suggestions": [],
                    "total": 0,
                    "high_score_count": 0,
                })
                return

            total_objectives = len(all_objectives)
            yield format_sse_event("phase", {
                "stage": "objectives_loaded",
                "message": f"Found {total_objectives} objectives, sending to AI for analysis...",
                "percent": 35,
                "total_objectives": total_objectives,
            })

            # Phase 3: LLM call
            yield format_sse_event("phase", {
                "stage": "analyzing",
                "message": "AI is analyzing and ranking objectives... This may take a moment.",
                "percent": 50,
            })

            ranked = await ai_generator.rank_objectives_with_llm(
                question["question_text"], all_objectives
            )

            high_score_count = len([r for r in ranked if r["score"] >= 60])

            yield format_sse_event("all_done", {
                "suggestions": ranked,
                "total": len(ranked),
                "high_score_count": high_score_count,
            })

        except Exception as e:
            logger.error(f"Fatal error in objectives stream: {e}", exc_info=True)
            yield format_sse_event("fatal_error", {"message": str(e)})

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/{question_id}/generate-objective", response_class=JSONResponse)
async def generate_objective_for_question(question_id: str):
    """
    Generates a learning objective for a question using AI and computes similarity score.
    """
    logger.info(f"Generating learning objective for question_id: {question_id}")
    try:
        question_data = db.load_question_details(question_id)
        if not question_data:
            raise HTTPException(status_code=404, detail="Question not found")
        
        question_text = question_data.get('question_text', '')
        if not question_text:
            raise HTTPException(status_code=400, detail="Question text is empty")
        
        # Generate objective using AI
        objective_text = await ai_generator.generate_objective_from_question(question_text)
        
        # Compute similarity score between question and generated objective
        similarity_score = await ai_generator.compute_similarity_score(question_text, objective_text)
        
        return {
            "objective": objective_text, 
            "score": similarity_score,
            "success": True
        }
    except Exception as e:
        logger.error(f"Error generating objective: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate objective.")


@router.post("/{question_id}/check-objective-similarity", response_class=JSONResponse)
async def check_objective_similarity(question_id: str, data: dict):
    """
    Computes similarity score between a question and a provided objective text.
    """
    logger.info(f"Checking objective similarity for question_id: {question_id}")
    try:
        question_data = db.load_question_details(question_id)
        if not question_data:
            raise HTTPException(status_code=404, detail="Question not found")
        
        question_text = question_data.get('question_text', '')
        if not question_text:
            raise HTTPException(status_code=400, detail="Question text is empty")
        
        objective_text = data.get('objective_text', '').strip()
        if not objective_text:
            raise HTTPException(status_code=400, detail="Objective text is required")
        
        if len(objective_text) < 20:
            raise HTTPException(status_code=400, detail="Objective text must be at least 20 characters")
        
        # Compute similarity score
        similarity_score = await ai_generator.compute_similarity_score(question_text, objective_text)
        
        return {
            "score": similarity_score,
            "success": True
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking similarity: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to compute similarity score.")


@router.get("/{question_id}/associate-objectives", response_class=HTMLResponse)
async def associate_objectives_page(request: Request, question_id: str):
    """
    Renders the associate objectives page for a question.
    Shows all objectives with AI suggestions pre-selected.
    """
    logger.info(f"Loading associate objectives page for question_id: {question_id}")
    try:
        question_data = db.load_question_details(question_id)
        if not question_data:
            raise HTTPException(status_code=404, detail="Question not found")
        
        return templates.TemplateResponse(
            "associate_objectives.html",
            {
                "request": request,
                "question": question_data,
                "current_objective_ids": question_data.get('objective_ids', [])
            },
        )
    except Exception as e:
        logger.error(f"Error loading associate objectives page: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to load page.")


@router.post("/{question_id}/associate-objectives", response_class=JSONResponse)
async def save_objective_associations(question_id: str, data: dict):
    """
    Saves the objective associations for a question.
    Receives a list of objective IDs and updates the associations.
    """
    logger.info(f"Saving objective associations for question_id: {question_id}")
    try:
        question = db.load_question_details(question_id)
        if not question:
            raise HTTPException(status_code=404, detail="Question not found")
        
        objective_ids = data.get('objective_ids', [])
        logger.info(f"Updating question {question_id} with {len(objective_ids)} objectives")
        
        db.replace_question_objectives(question_id, objective_ids)
        
        logger.info(f"Successfully updated objective associations for question {question_id}")
        return {"success": True, "message": "Objectives updated successfully"}
        
    except Exception as e:
        logger.error(f"Error saving objective associations: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to save objectives.")

