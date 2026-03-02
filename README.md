# Question App

A comprehensive web application for managing Canvas LMS quiz questions with AI-powered feedback generation and an intelligent chat assistant using RAG (Retrieval-Augmented Generation).

## 🏗️ Project Structure

This project follows Poetry best practices with a well-organized directory structure:

```
questionapp/
├── src/
│   └── question_app/          # Main application package
│       ├── __init__.py
│       ├── main.py           # FastAPI application entry point
│       ├── api/              # API endpoints and routers
│       │   ├── __init__.py   # API module exports
│       │   ├── canvas.py     # Canvas LMS integration endpoints
│       │   ├── questions.py  # Question CRUD endpoints
│       │   ├── chat.py       # RAG-based chat endpoints
│       │   ├── vector_store.py # Vector store operations endpoints
│       │   ├── objectives.py # Learning objectives management endpoints
│       │   ├── system_prompt.py  # System prompt management endpoints
│       │   └── debug.py      # Debugging and testing endpoints
│       ├── core/             # Core configuration and app setup
│       │   ├── __init__.py   # Core module exports
│       │   ├── config.py     # Centralized configuration management
│       │   ├── logging.py    # Centralized logging setup
│       │   └── app.py        # FastAPI application setup
│       ├── models/           # Pydantic models and data structures
│       ├── services/         # Business logic and external integrations
│       └── utils/            # Utility functions and helpers
├── scripts/                  # Development and build scripts
│   ├── __init__.py
│   ├── build_docs.py
│   ├── build_docs_simple.py
│   ├── docs_and_serve.py
│   ├── format_code.py
│   ├── lint_code.py
│   ├── run_tests.py
│   ├── serve_docs.py
│   └── type_check.py
├── config/                   # Configuration files
│   ├── system_prompt.txt
│   ├── chat_system_prompt.txt
│   └── chat_welcome_message.txt
├── data/                     # Data files
│   ├── quiz_questions.json
│   └── learning_objectives.json
├── docs/                     # Documentation
├── static/                   # Static web assets
├── templates/                # HTML templates
├── tests/                    # Test suite
├── vector_store/             # Vector database storage
├── .vscode/                  # VS Code configuration
│   ├── settings.json         # Python interpreter, PYTHONPATH, formatting
│   ├── tasks.json            # Development tasks (install, test, format, etc.)
│   ├── launch.json           # Debug configurations
│   └── extensions.json       # Recommended VS Code extensions
├── pyproject.toml           # Poetry configuration
├── poetry.lock              # Dependency lock file
└── README.md                # This file
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Poetry (for dependency management)
- Canvas LMS API access
- Azure OpenAI API access (optional, for AI features)

### Installation

1. **Clone the repository:**

   ```bash
   git clone <repository-url>
   cd questionapp
   ```

2. **Install dependencies:**

   ```bash
   poetry install
   ```

3. **Set up environment variables:**
   Create a `.env` file in the project root with your configuration:

   ```env
   CANVAS_BASE_URL=https://canvas.vt.edu
   CANVAS_API_TOKEN=your_canvas_token
   COURSE_ID=your_course_id
   QUIZ_ID=your_quiz_id
   AZURE_OPENAI_ENDPOINT=your_azure_endpoint
   AZURE_OPENAI_DEPLOYMENT_ID=your_deployment_id
   AZURE_OPENAI_API_VERSION=2023-12-01-preview
   AZURE_OPENAI_SUBSCRIPTION_KEY=your_subscription_key
   OLLAMA_HOST=http://localhost:11434
   OLLAMA_EMBEDDING_MODEL=nomic-embed-text
   ```

   Optional: if you plan to use local embeddings via Ollama, start the Ollama
   service in a new terminal and then pull the embedding model in your current
   terminal:

   ```bash
   # New terminal - keep this running
   ollama serve

   # Original terminal
   ollama pull nomic-embed-text
   ```

4. **Run the application:**

   ```bash
   # Development mode
   poetry run dev

   # Production mode
   poetry run start
   ```

## 🐳 Docker Setup (Recommended)

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) (20.10+)
- [Docker Compose](https://docs.docker.com/compose/install/) (2.0+)

### Quick Start with Docker

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd Merged-App
   ```

2. **Configure environment variables:**
   ```bash
   # Copy the template
   cp .env.docker.template .env

   # Edit .env and add your API credentials:
   # - AZURE_OPENAI_ENDPOINT
   # - AZURE_OPENAI_DEPLOYMENT_ID
   # - AZURE_OPENAI_SUBSCRIPTION_KEY
   # - CANVAS_BASE_URL
   # - CANVAS_API_TOKEN
   # - COURSE_ID
   # - QUIZ_ID
   nano .env  # or use your preferred editor
   ```

3. **Start all services:**
   ```bash
   docker compose up -d --build
   ```

   This will:
   - Build the FastAPI backend with all dependencies
   - Start PostgreSQL with pgvector (vector database)
   - Pull and start Ollama (downloads ~274MB embedding model)

4. **Seed the database:**

   The database starts empty. Follow these steps to populate it:

   a. **Fetch questions from Canvas:** Open http://localhost:8080, select your course and quiz in the configuration panel, then click **Fetch Questions**. This pulls all questions from Canvas into the database with dedup support (safe to click multiple times).

   b. **Import learning objectives and associations:**
      ```bash
      docker exec question-app-backend poetry run python scripts/import_objectives.py prod
      ```
      This reads `data/objectives_export.json` (included in the repo) and creates all learning objectives and links them to the fetched questions using stable Canvas IDs.

   c. **Build the vector store (for RAG chat):** Click **More Options > Create Vector Store** in the UI header, or run:
      ```bash
      curl -X POST http://localhost:8080/vector-store/create
      ```

5. **Access the application:**
   - **Application:** http://localhost:8080
   - PostgreSQL: `localhost:5432` (user: `app_user`, db: `socratic_tutor`)
   - Ollama: http://localhost:11434

**That's it!** Your application is ready with all questions, objectives, and embeddings.

> **Note on embeddings:** After the initial vector store build, embeddings are automatically generated when you create or edit questions. When you fetch new questions from Canvas, embeddings for any newly added questions are generated in the background with a progress indicator.

### Docker Commands Reference

```bash
# Start services
docker-compose up              # Foreground (see logs)
docker-compose up -d           # Background (detached)

# Stop services
docker-compose down            # Stop and remove containers
docker-compose down -v         # Stop and remove containers + volumes (⚠️ deletes data)

# View logs
docker-compose logs            # All services
docker-compose logs backend    # Specific service
docker-compose logs -f         # Follow logs (live)

# Rebuild after code changes
docker-compose up --build      # Rebuild and start

# Execute commands in containers
docker-compose exec backend poetry run test        # Run tests
docker-compose exec backend poetry run lint        # Run linter
docker-compose exec backend bash                   # Open shell

# Check service status
docker-compose ps              # List running services
docker-compose top             # Show running processes

# Restart specific service
docker-compose restart backend
```

### Docker Development Workflow

**Hot Reload Enabled:** Code changes in `src/`, `templates/`, and `static/` are automatically reflected without rebuilding.

**Persistent Data:**
- **PostgreSQL database:** Stored in Docker volume `question-app-postgres-data` (questions, objectives, embeddings)
- **JSON backups:** `./data/quiz_questions.json` and `./data/objectives_export.json` on your host machine
- **Ollama models:** Stored in Docker volume `question-app-ollama-models`

**Service Communication:** Services communicate using Docker DNS:
- Backend connects to `postgres:5432` (not `localhost:5432`)
- Backend connects to `ollama:11434` (not `localhost:11434`)

### Exporting & Sharing Data

Objectives and question associations are portable via JSON export/import:

**Export (save your curated data):**
```bash
docker exec question-app-backend poetry run python scripts/export_objectives.py prod
# Creates data/objectives_export.json — commit this to share with others
```

**Import (on a fresh instance):**
```bash
# After fetching questions from Canvas:
docker exec question-app-backend poetry run python scripts/import_objectives.py prod
```

**Database backup (full PostgreSQL dump):**
```bash
docker exec question-app-postgres pg_dump -U app_user socratic_tutor > backups/backup-$(date +%Y%m%d).sql
```

### Troubleshooting Docker Setup

**Issue: Port already in use**
```bash
# Check what's using the port
lsof -i :8080  # or :8000, :11434

# Stop the conflicting service or change port in docker-compose.yml
```

**Issue: Ollama model not downloading**
```bash
# Check Ollama logs
docker-compose logs ollama

# Manually pull model
docker-compose exec ollama ollama pull nomic-embed-text
```

**Issue: Services can't communicate**
```bash
# Check network
docker network inspect question-app-network

# Verify service names resolve
docker compose exec backend ping postgres
docker compose exec backend ping ollama
```

**Clean slate (⚠️ deletes all data):**
```bash
# Remove everything and start fresh
docker-compose down -v
docker-compose up --build
```

## 🛠️ Development

### VS Code Configuration

This project includes comprehensive VS Code configuration for an optimal development experience:

- **`.vscode/settings.json`** - Python interpreter, PYTHONPATH, formatting, testing configuration
- **`.vscode/tasks.json`** - Pre-configured tasks for Poetry install, dev server, tests, lint, format, docs
- **`.vscode/launch.json`** - Debug configurations for API and tests
- **`.vscode/extensions.json`** - Recommended VS Code extensions

**Key Features:**

- ✅ **Type Safety**: 100% Pyright compliance, 80% Mypy compliance
- ✅ **Integrated Testing**: Pytest integration with Test Explorer
- ✅ **Debugging**: Full debugging support for FastAPI and tests
- ✅ **Code Quality**: Black formatting, isort imports, flake8 linting
- ✅ **Documentation**: Sphinx documentation building and serving

**Quick Start with VS Code:**

1. Open the project in VS Code
2. Install recommended extensions when prompted
3. Use Command Palette (`Cmd/Ctrl + Shift + P`) to access tasks:
   - `Tasks: Run Task` → "Poetry: Install"
   - `Tasks: Run Task` → "Run: Dev Server"
   - `Tasks: Run Task` → "Test: Pytest"
   - `Tasks: Run Task` → "Format: black+isort"

### Available Commands

The project includes several Poetry scripts for development tasks:

```bash
# Application
poetry run start          # Start the application
poetry run dev            # Start in development mode

# Testing
poetry run test           # Run all tests
poetry run test --type unit
poetry run test --type integration
poetry run test --type ai
poetry run test --type api

# Code Quality
poetry run format         # Format code with Black
poetry run lint           # Lint code with flake8
poetry run type-check     # Type checking with mypy

# Documentation
poetry run docs           # Build documentation
poetry run docs-simple    # Build docs without make
poetry run docs-serve     # Serve docs locally
```

### Development Workflow

1. **Code Formatting:**

   ```bash
   poetry run format
   ```

2. **Linting:**

   ```bash
   poetry run lint
   ```

3. **Type Checking:**

   ```bash
   poetry run type-check
   ```

4. **Running Tests:**

   ```bash
   poetry run test
   ```

5. **Building Documentation:**
   ```bash
   poetry run docs-serve
   ```

## 📚 Documentation

Documentation is built using Sphinx and can be accessed by running:

```bash
poetry run docs-serve
```

This will build the documentation and serve it locally at `http://localhost:8000`.

## 🔒 Type Safety

This project maintains high standards for type safety and code quality:

### Type Checking Results

- **Pyright**: 0 errors (100% compliance)
- **Mypy**: 3 remaining errors (80% improvement from 15 errors)
- **Remaining mypy errors**: Known limitations with complex nested logic (false positives)

### Type Safety Features

- ✅ **Comprehensive type annotations** across all modules
- ✅ **Pydantic models** for data validation
- ✅ **Type guards** for runtime type checking
- ✅ **Proper error handling** with typed exceptions
- ✅ **Integration with VS Code** for real-time type checking

### Recent Type Safety Improvements

- Fixed Canvas API string indexing issues
- Resolved Vector Store embeddings type compatibility
- Improved test exception handling with proper HTTPException types
- Added comprehensive type annotations to AI service
- Enhanced UploadFile handling in chat API

## 🧪 Testing

The project includes comprehensive tests organized by type:

- **Unit Tests:** Test individual functions and classes
- **Integration Tests:** Test component interactions
- **AI Tests:** Test AI integration features
- **API Tests:** Test API endpoints

Run specific test types:

```bash
poetry run test --type unit
poetry run test --type integration
poetry run test --type ai
poetry run test --type api
```

## 🔧 Configuration

Configuration files are stored in the `config/` directory:

- `system_prompt.txt` - Main system prompt for AI interactions
- `chat_system_prompt.txt` - Chat assistant system prompt
- `chat_welcome_message.txt` - Welcome message for chat interface

## 📁 Data Management

Data files are stored in the `data/` directory:

- `quiz_questions.json` - Quiz questions data
- `learning_objectives.json` - Learning objectives data

## 🏗️ Architecture

The application follows a modular architecture:

- **API Layer** (`src/question_app/api/`): FastAPI endpoints and routers
  - **Canvas API** (`canvas.py`): Canvas LMS integration endpoints
  - **Questions API** (`questions.py`): Question CRUD operations
  - **Chat API** (`chat.py`): RAG-based chat functionality
  - **Vector Store API** (`vector_store.py`): Vector store operations and semantic search
  - **Objectives API** (`objectives.py`): Learning objectives management
  - **Debug API** (`debug.py`): Debugging and testing endpoints
  - Additional API modules can be added for other functionality
- **Core Layer** (`src/question_app/core/`): Core application logic
- **Models Layer** (`src/question_app/models/`): Data models and schemas
- **Services Layer** (`src/question_app/services/`): Business logic and external integrations
- **Utils Layer** (`src/question_app/utils/`): Utility functions and helpers

## 🔌 API Structure

The API is organized into focused modules for better maintainability:

### Canvas Integration (`/api/*`)

- `GET /api/courses` - Get all available courses
- `GET /api/courses/{course_id}/quizzes` - Get all quizzes for a specific course
- `POST /api/configuration` - Update course and quiz configuration
- `POST /api/fetch-questions` - Fetch questions from Canvas API

### Question Management (`/*`)

- `GET /` - Main application page
- `GET /questions/{id}` - Question edit page
- `GET /questions/new` - New question creation page
- `POST /questions/{id}/generate-feedback` - Generate AI feedback
- And more...

### Chat Interface (`/chat/*`)

- `GET /chat/` - Chat interface page
- `POST /chat/message` - Process chat messages with RAG
- `GET /chat/system-prompt` - Chat system prompt management
- `GET /chat/welcome-message` - Welcome message management

### Vector Store Operations (`/vector-store/*`)

- `POST /vector-store/create` - Create vector store from questions
- `GET /vector-store/search` - Search vector store for relevant content
- `GET /vector-store/status` - Get vector store status
- `DELETE /vector-store/` - Delete vector store

### Learning Objectives Management (`/objectives/*`)

- `GET /objectives/` - Learning objectives management page
- `POST /objectives/` - Save learning objectives

### Debug and Testing (`/debug/*`)

- `GET /debug/question/{question_id}` - Inspect specific question details
- `GET /debug/config` - Check application configuration status
- `GET /debug/ollama-test` - Test Ollama connection and model availability

See `docs/api_structure.md` for detailed API documentation.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## 📄 Documentation

### Available Scripts

- `poetry run docs` - Build HTML documentation
- `poetry run docs-simple` - Build docs without make dependency
- `poetry run docs-serve` - Serve documentation locally

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👥 Authors

- **Bryce Kayanuma** - _Initial work_ - [BrycePK@vt.edu](mailto:BrycePK@vt.edu)
- **Robert Fentress** - [learn@vt.edu](mailto:learn@vt.edu)

## 🤖 Setting Up RAG Pipeline for Conversations with Tutor

This section provides step-by-step instructions to set up the RAG (Retrieval-Augmented Generation) pipeline for conversational interactions with the Socratic tutor. This process involves multiple terminal instances, so follow each step carefully.

### Prerequisites

- Docker installed on your machine
- Poetry installed
- Ollama installed

### Setup Steps

1. **Start ChromaDB Service**

   Navigate to the root directory of the project (`questionapp`) and run:

   ```bash
   docker run -d \
     --name socratic_chroma \
     -p 8001:8000 \
     -v "$(pwd)/data:/chroma/data" \
     chromadb/chroma:0.4.24
   ```

   This starts the ChromaDB service in a Docker container with persistent storage mounted to your local `data` directory.

2. **Verify Container is Running**

   In the same terminal, verify the container is running:

   ```bash
   docker ps
   ```

3. **Start Ollama Service**

   Open a **new terminal instance** and start the Ollama service:

   ```bash
   ollama serve
   ```

   Keep this terminal running.

4. **Pull Embedding Model**

   Open another **new terminal instance** and pull the required embedding model (only needs to be done once):

   ```bash
   ollama pull nomic-embed-text
   ```

5. **Start the Application**

   Open another **new terminal instance** and start the backend service:

   ```bash
   poetry run dev
   ```

   Keep this terminal running and wait for the backend service to start completely.

6. **Create Vector Store**

   Open another **new terminal instance** and create the vector store:

   ```bash
   curl -X POST http://localhost:8080/vector-store/create
   ```

   You should see success messages in the terminal where the backend is running.
