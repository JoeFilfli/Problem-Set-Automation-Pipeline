# Problem-Set Automation Pipeline

An AI-powered educational platform that automates the creation, distribution, grading, and analysis of problem sets using intelligent agent orchestration and RAG (Retrieval-Augmented Generation) technology.

## 📋 Overview

This system combines a **FastAPI backend** with a **Next.js frontend** to provide comprehensive tools for both professors and students:

- **For Professors**: Generate problem sets from course materials, create MCQs, grade submissions automatically, and analyze student performance
- **For Students**: Solve problems with AI-guided assistance, submit work, receive feedback, and compete in "Beat the AI" challenges

## ✨ Key Features

### 🎓 Professor Tools
- **AI-Powered Problem Generation**: Automatically generate problem sets from uploaded course materials (PDFs, textbooks, notes)
- **RAG Integration**: Uses vector embeddings and semantic search to find relevant content for problem creation
- **Intelligent Grading**: Automated grading with detailed feedback using AI agents
- **MCQ Generator**: Create multiple-choice questions aligned with course content
- **Analytics Dashboard**: Track student performance, identify struggling topics, and monitor engagement
- **Materials Management**: Upload and organize course materials for RAG ingestion

### 🧑‍🎓 Student Tools
- **Guided Problem Solving**: Step-by-step AI assistance while solving problems
- **Interactive Workspace**: Clean interface for working through problem sets
- **Submission System**: Submit solutions and receive automated grades with feedback
- **Beat the AI**: Challenge mode where students compete against AI-generated solutions
- **Course Feedback**: Provide feedback on course content and difficulty
- **Grades Tracking**: View performance across all problem sets

### 🔧 Technical Features
- **RAG Pipeline**: Semantic chunking, vector storage (ChromaDB), and intelligent retrieval
- **Agent Orchestration**: Multiple specialized AI agents work together to analyze, generate, and grade
- **PDF Processing**: Extract and process educational materials (PyMuPDF)
- **Image Support**: Handle mathematical diagrams and figures
- **Real-time Updates**: Live feedback during problem-solving sessions

## 🏗️ Architecture

```
Problem-Set-Automation-Pipeline/
│
├── fastapi_backend/          # Python/FastAPI backend
│   ├── api/                  # API routes and endpoints
│   │   ├── index.py          # FastAPI app entry point
│   │   ├── dependencies.py   # Shared dependencies (vector store, etc.)
│   │   └── routers/          # Modular route handlers
│   │       ├── materials.py      # Upload & manage course materials
│   │       ├── problem_sets.py   # Generate & retrieve problem sets
│   │       ├── submissions.py    # Submit & grade student work
│   │       ├── rag.py            # RAG queries & document ingestion
│   │       ├── mcqs.py           # Generate multiple-choice questions
│   │       ├── analytics.py      # Student performance analytics
│   │       ├── guided_solve.py   # AI-assisted problem solving
│   │       ├── beat_ai.py        # "Beat the AI" challenges
│   │       ├── feedback.py       # Course feedback collection
│   │       └── images.py         # Image upload & retrieval
│   ├── api_storage/          # File storage for problem sets, submissions, etc.
│   ├── rag_db/               # ChromaDB vector database
│   ├── sample_materials/     # Example course materials
│   ├── agent_orchestrator.py # Multi-agent coordination system
│   ├── problem_set_generator.py # Problem generation logic
│   ├── grading_agents.py     # Automated grading system
│   ├── vector_store.py       # RAG vector operations
│   ├── pdf_extractor.py      # PDF parsing and text extraction
│   ├── chunker.py            # Semantic text chunking
│   └── models.py             # Data models
│
└── nextjs_frontend/          # Next.js/React/TypeScript frontend
    ├── app/                  # Next.js 13+ app directory
    │   ├── professor/        # Professor dashboard and tools
    │   │   ├── materials/        # Material management
    │   │   ├── problem-sets/     # Problem set creation
    │   │   ├── mcqs/             # MCQ generation
    │   │   ├── analytics/        # Performance analytics
    │   │   └── beat-ai/          # Create AI challenges
    │   ├── student/          # Student interface
    │   │   ├── problem-sets/     # View assignments
    │   │   ├── workspace/        # Solve problems
    │   │   ├── solve/            # Guided solving
    │   │   ├── grades/           # View grades
    │   │   ├── beat-ai/          # Take challenges
    │   │   └── feedback/         # Submit feedback
    │   └── rag-lab/          # RAG testing interface
    ├── components/           # Reusable React components
    └── lib/                  # API clients and utilities
        ├── api/              # API client functions
        ├── types/            # TypeScript type definitions
        └── utils/            # Utility functions
```

### Backend Router Details

Each router handles specific functionality with RESTful endpoints:

| Router | Prefix | Purpose |
|--------|--------|---------|
| **materials** | `/api/py` | Upload PDFs, list materials, delete documents |
| **problem_sets** | `/api/py` | Generate problem sets, retrieve by ID, list all |
| **submissions** | `/api/py` | Submit student work, auto-grade, retrieve grades |
| **rag** | `/api/py` | Query RAG database, ingest documents, semantic search |
| **mcqs** | `/api/py` | Generate multiple-choice questions from materials |
| **analytics** | `/api/py/analytics` | Performance metrics, topic analysis, student insights |
| **guided_solve** | `/api/py/guided` | AI hints, step-by-step guidance, chat sessions |
| **beat_ai** | `/api/beat-ai` | Create challenges, submit attempts, compare with AI |
| **feedback** | `/api/feedback` | Collect course feedback, retrieve aggregated results |
| **images** | `/api/py` | Upload images, retrieve by ID, handle diagrams |

## 🚀 Getting Started

You can run this project either with **Docker** (recommended for easy setup) or **manually** (for development).

### Prerequisites

#### For Docker Setup (Recommended)
- **Docker** and **Docker Compose**
- **OpenAI API Key** (for AI agents)

#### For Manual Setup
- **Python 3.10+** (3.12 recommended)
- **Node.js 18+** and **npm**
- **OpenAI API Key** (for AI agents)

---

## 🐳 Docker Setup (Recommended)

The easiest way to get started is using Docker. This handles all dependencies automatically.

### Quick Start with Docker

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd Problem-Set-Automation-Pipeline
   ```

2. **Set up environment variables:**
   ```bash
   # Copy the example file
   cp fastapi_backend/.env.example fastapi_backend/.env
   
   # Edit the file and add your OpenAI API key
   # On Windows: notepad fastapi_backend\.env
   # On macOS/Linux: nano fastapi_backend/.env
   ```
   
   Add your OpenAI API key:
   ```env
   OPENAI_API_KEY=your_actual_api_key_here
   ```

3. **Start the application:**
   ```bash
   # Start both services
   docker-compose up
   
   # Or run in background
   docker-compose up -d
   ```

4. **Access the application:**
   - **Frontend**: http://localhost:3000
   - **Backend API**: http://localhost:8000
   - **API Docs**: http://localhost:8000/api/py/docs

5. **View logs:**
   ```bash
   # View all logs
   docker-compose logs -f
   
   # View backend logs only
   docker-compose logs -f backend
   
   # View frontend logs only
   docker-compose logs -f frontend
   ```

6. **Stop the application:**
   ```bash
   # Stop containers
   docker-compose down
   
   # Stop and remove all data (clean restart)
   docker-compose down -v
   ```

### Docker Commands Cheat Sheet

```bash
# Rebuild containers after code changes
docker-compose up --build

# Restart a specific service
docker-compose restart backend

# Execute commands inside containers
docker-compose exec backend python -c "print('Hello from backend')"
docker-compose exec frontend npm run lint

# View container status
docker-compose ps

# Remove everything including volumes
docker-compose down -v --remove-orphans
```

### Data Persistence

Docker volumes are used to persist data across container restarts:

- **`rag_db/`**: Vector database for RAG
- **`api_storage/`**: Problem sets, submissions, MCQs, etc.
- **`sample_materials/`**: Course materials
- **`student_work/`**: Student submissions

Data persists even when containers are stopped. To completely reset:

```bash
docker-compose down -v
```

---

## 🔧 Manual Setup (Development)

If you prefer to run the services directly without Docker:

### Prerequisites

- **Python 3.10+** (3.12 recommended)
- **Node.js 18+** and **npm**
- **OpenAI API Key** (for AI agents)

### Backend Setup

1. **Navigate to backend directory:**
   ```bash
   cd fastapi_backend
   ```

2. **Create and activate virtual environment:**
   ```bash
   python -m venv venv
   
   # Windows
   .\venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**
   Create a `.env` file in `fastapi_backend/`:
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   ```

5. **Start the backend server:**
   ```bash
   uvicorn api.index:app --reload --host 0.0.0.0 --port 8000
   ```

   The API will be available at `http://localhost:8000`
   API documentation: `http://localhost:8000/api/py/docs`

### Frontend Setup

1. **Navigate to frontend directory:**
   ```bash
   cd nextjs_frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Start the development server:**
   ```bash
   npm run dev
   ```

   The application will be available at `http://localhost:3000`

### Initial Setup

1. **Upload Course Materials** (Professor):
   - Navigate to the Materials page
   - Upload PDFs of textbooks, lecture notes, or syllabi
   - The RAG system will automatically ingest and index the content

2. **Generate a Problem Set**:
   - Go to the Problem Sets page
   - Select topics or chapters to focus on
   - Configure difficulty level and number of problems
   - Let the AI generate a customized problem set

3. **Students Can Start Solving**:
   - View available problem sets
   - Use guided solving mode for hints and explanations
   - Submit solutions for automated grading

## 🔌 API Endpoints

### Materials
- `POST /api/py/materials/upload` - Upload course materials
- `GET /api/py/materials/list` - List all materials
- `DELETE /api/py/materials/{filename}` - Delete material

### Problem Sets
- `POST /api/py/problem-sets/generate` - Generate new problem set
- `GET /api/py/problem-sets/list` - List all problem sets
- `GET /api/py/problem-sets/{ps_id}` - Get specific problem set

### Submissions
- `POST /api/py/submissions/submit` - Submit student work
- `POST /api/py/submissions/grade` - Grade submission
- `GET /api/py/submissions/{ps_id}` - Get submission for problem set

### RAG
- `POST /api/py/rag/query` - Query the RAG system
- `POST /api/py/rag/ingest` - Ingest new materials

### MCQs
- `POST /api/py/mcqs/generate` - Generate multiple-choice questions
- `GET /api/py/mcqs/list` - List saved MCQs

### Analytics
- `GET /api/py/analytics/overview` - Get performance analytics
- `GET /api/py/analytics/topics` - Topic-level analysis

### Beat AI
- `POST /api/py/beat-ai/generate` - Create Beat AI challenge
- `POST /api/py/beat-ai/submit` - Submit challenge attempt

## 🧠 How It Works

### RAG Pipeline

1. **Document Ingestion**: PDFs are uploaded and text is extracted
2. **Semantic Chunking**: Content is split into meaningful chunks using AI
3. **Vector Embedding**: Chunks are embedded using OpenAI embeddings
4. **Storage**: Vectors stored in ChromaDB for fast retrieval
5. **Query**: When generating problems, relevant chunks are retrieved

### Agent Orchestration

The system uses multiple specialized AI agents:

- **Analyzer Agent**: Examines course materials and identifies key topics
- **Problem Generator Agent**: Creates problems based on topics and difficulty
- **Solution Agent**: Generates detailed solutions with steps
- **Grading Agent**: Evaluates student submissions and provides feedback
- **Hint Agent**: Provides context-aware hints during guided solving

### Problem Generation Flow

```
Course Materials → RAG Retrieval → Topic Analysis → 
Problem Generation → Solution Generation → PDF Export
```

### Grading Flow

```
Student Submission → Extract Answers → Compare with Solutions → 
AI Evaluation → Detailed Feedback → Grade Calculation
```

## 📦 Technologies Used

### Backend
- **FastAPI**: Modern Python web framework
- **OpenAI API**: GPT-4 for intelligent agents
- **ChromaDB**: Vector database for RAG
- **PyMuPDF**: PDF parsing and generation
- **ReportLab**: PDF creation with formatting
- **NumPy/Matplotlib**: Data analysis and visualization
- **Docker**: Containerization for easy deployment

### Frontend
- **Next.js 15**: React framework with App Router
- **TypeScript**: Type-safe development
- **TailwindCSS**: Utility-first styling
- **React Markdown**: Render formatted content
- **KaTeX**: Mathematical equation rendering
- **Docker**: Containerization for easy deployment

## 📁 Data Storage

All data is stored locally in `fastapi_backend/api_storage/`:

- `problem_sets/` - Generated problem sets (JSON)
- `submissions/` - Student submissions (JSON)
- `saved_mcqs/` - Multiple-choice questions (JSON)
- `beat_ai_challenges/` - Beat AI challenges (JSON)
- `beat_ai_submissions/` - Beat AI attempts (JSON)
- `feedback/` - Course feedback (JSON)
- `images/` - Uploaded images and diagrams

## 🎯 Use Cases

1. **Homework Generation**: Create weekly problem sets aligned with lectures
2. **Exam Preparation**: Generate practice problems covering multiple topics
3. **Adaptive Learning**: Identify weak areas and generate targeted problems
4. **Flipped Classroom**: Students solve problems with AI guidance before class
5. **Assessment**: Automated grading saves instructor time
6. **Engagement**: Beat the AI mode gamifies learning

## 🔒 Security Notes

- Store your OpenAI API key securely in `.env` files
- Never commit `.env` files to version control
- The `.gitignore` is configured to exclude sensitive files
- Consider adding authentication for production deployment

## 🐛 Troubleshooting

### Windows Installation Issues

If you encounter errors installing NumPy/Matplotlib:
```bash
pip install numpy
pip install --only-binary :all: matplotlib
pip install -r requirements.txt
```

### ChromaDB Errors

If ChromaDB fails to initialize, delete the `rag_db` folder and re-ingest materials.

### OpenAI API Errors

- Verify your API key is correct
- Check your OpenAI account has available credits
- Ensure you're using a supported model (GPT-4 recommended)

### Port Conflicts

If ports 3000 or 8000 are in use:
```bash
# Backend on different port
uvicorn api.index:app --port 8001

# Frontend on different port
PORT=3001 npm run dev
```

## 🤝 Contributing

Contributions are welcome! This is an educational tool designed to make teaching and learning more efficient.

## 📄 License

MIT License - Copyright (c) 2023 Diego Valdez

See [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with OpenAI's GPT-4 for intelligent agent capabilities
- ChromaDB for efficient vector storage and retrieval
- FastAPI and Next.js communities for excellent frameworks

## 📧 Support

For issues or questions:
1. Check the API docs at `/api/py/docs`
2. Review error messages in terminal/console
3. Search for similar issues on GitHub
4. Create a new issue with detailed error information

---

**Happy Teaching and Learning! 🎓✨**

