"""
Canvas Quiz Manager - A Comprehensive Web Application

This module provides a FastAPI-based web application for managing Canvas LMS quiz
questions with AI-powered feedback generation and an intelligent chat assistant
using RAG (Retrieval-Augmented Generation).

The application integrates with:
- Canvas LMS API for fetching quiz questions
- Azure OpenAI for AI-powered feedback generation
- Ollama for local embedding generation
- PostgreSQL + pgvector for vector storage and semantic search
- FastAPI for web API and frontend

Key Features:
- Fetch and manage quiz questions from Canvas LMS
- Generate educational feedback using AI
- Intelligent chat assistant with RAG capabilities
- Vector store operations and semantic search
- Learning objectives management
- System prompt customization
- Comprehensive type safety with Pyright and Mypy
- VS Code integration with debugging and task automation
- Enhanced error handling and validation

Architecture:
- Core configuration and app setup in core/ module
- Modular API endpoints in api/ module
- Business logic in services/ module
- Utility functions in utils/ module

Authors:
  - Bryce Kayanuma <BrycePK@vt.edu>
  - Robert Fentress <learn@vt.edu>
Version: 0.3.0

Recent Improvements (v0.3.0):
- Enhanced type safety: 100% Pyright compliance, 80% Mypy improvement
- VS Code integration with comprehensive configuration
- Fixed feedback generation for new questions
- Improved error handling and validation
- Enhanced debugging capabilities
"""

import uvicorn
import markdown
from fastapi import HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Import core modules
from .core import config, create_app, get_logger, get_templates, register_routers


#Import DB Manager
from .services.database import get_database_manager

# TODO: Test fastapi_mpc https://github.com/tadata-org/fastapi_mcp
# TODO: Offload vector store to S3 Vector Bucket


# Set up logging
logger = get_logger(__name__)

#Initialize DB
logger.info(f"Initializing Database Manager for main app...")
db = get_database_manager()

# Create and configure the application
app = create_app()
register_routers(app)


# Routes
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """
    Home page endpoint displaying all quiz questions.

    This endpoint serves the main application page that displays all questions
    in a table format with options to edit, delete, and generate AI feedback.

    Args:
        request (Request): FastAPI request object.

    Returns:
        HTMLResponse: Rendered index.html template with questions data.

    Raises:
        HTTPException: If there's an error loading questions or rendering the template.

    Note:
        The response includes cache-busting headers to prevent browser caching issues.
        The template receives questions data, course ID, and quiz ID for display.
    """
    try:
        questions = db.list_all_questions()
        templates = get_templates(app)

        # Convert markdown in question_text to HTML for card preview
        import re
        md = markdown.Markdown(extensions=['fenced_code', 'codehilite'])
        # Tags that are safe in markdown output (block + inline formatting)
        SAFE_TAGS = {'p', 'br', 'strong', 'b', 'em', 'i', 'code', 'pre', 'span',
                     'ul', 'ol', 'li', 'a', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
                     'blockquote', 'hr', 'div', 'table', 'thead', 'tbody', 'tr',
                     'th', 'td', 'img', 'del', 's', 'sub', 'sup'}

        def sanitize_html(html_str):
            """Escape HTML tags that aren't safe markdown output."""
            def replace_tag(m):
                tag_name = m.group(1).strip().split()[0].lower().lstrip('/')
                if tag_name in SAFE_TAGS:
                    return m.group(0)
                return m.group(0).replace('<', '&lt;').replace('>', '&gt;')
            return re.sub(r'<(/?\s*[a-zA-Z][^>]*)>', replace_tag, html_str)

        for q in questions:
            if q.get('question_text'):
                q['question_text_html'] = sanitize_html(md.convert(q['question_text']))
                md.reset()
            else:
                q['question_text_html'] = ''

        return templates.TemplateResponse(
            "index.html",
            {
                "request" : request,
                "app_title" : config.APP_TITLE,
                "questions" : questions,
                "course_id" : config.COURSE_ID,
                "quiz_id" : config.QUIZ_ID
            }
        )
    except Exception as e:
        logger.error(f"Error loading home page: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to load questions: {str(e)}"
        )


def start():
    """
    Entry point for production server startup.

    This function starts the FastAPI application in production mode using uvicorn.
    The server runs on all interfaces (0.0.0.0) on port 8080.

    Note:
        This function is designed to be called from the command line or
        as a Poetry script entry point for production deployment.
    """
    uvicorn.run(app, host="0.0.0.0", port=8080)


def dev():
    """
    Entry point for development server startup with auto-reload.

    This function starts the FastAPI application in development mode using uvicorn
    with auto-reload enabled. The server runs on all interfaces (0.0.0.0) on port 8080.

    Note:
        This function is designed to be called from the command line or
        as a Poetry script entry point for development with hot reloading.
    """
    import os
    # Disable reload in Docker to avoid constant reload loops
    in_docker = os.environ.get('DOCKER_ENV', 'false') == 'true'

    uvicorn.run(
        "question_app.main:app",
        host="0.0.0.0",
        port=8080,
        reload=not in_docker,
        reload_dirs=["/app/src", "/app/templates"],
    )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
