# LMS Backend Architecture Design

## Table of Contents
1. [System Overview](#system-overview)
2. [Folder Structure](#folder-structure)
3. [Data Models](#data-models)
4. [API Endpoints](#api-endpoints)
5. [Security Design](#security-design)
6. [Workflows](#workflows)
7. [Database Schema](#database-schema)

---

## System Overview

**Tech Stack:**
- FastAPI (REST API)
- PostgreSQL (relational data: users, courses, submissions)
- ChromaDB (vector store for RAG)
- OpenAI API (LLM agents)
- JWT Authentication
- SQLAlchemy ORM

**Key Features:**
- Role-based access control (Professor, Student)
- Real-time progress tracking for document processing
- Asynchronous grading queue
- Analytics dashboard
- RAG-powered chatbot

---

## Folder Structure

```
fastapi_backend/
├── api/
│   ├── __init__.py
│   ├── deps.py                      # Dependencies (DB session, current user)
│   ├── index.py                     # Main app initialization
│   └── routes/
│       ├── __init__.py
│       ├── auth.py                  # Login, register, token refresh
│       ├── professor.py             # Professor-only endpoints
│       ├── student.py               # Student-only endpoints
│       └── shared.py                # Common endpoints (materials, RAG)
│
├── core/
│   ├── __init__.py
│   ├── config.py                    # Settings (env vars, database URLs)
│   ├── security.py                  # JWT, password hashing, permissions
│   └── database.py                  # SQLAlchemy session management
│
├── models/
│   ├── __init__.py
│   ├── user.py                      # User, Role models
│   ├── course.py                    # Course, CourseMaterial models
│   ├── problem_set.py               # ProblemSet, Problem models
│   ├── submission.py                # Submission, Grade models
│   └── analytics.py                 # AnalyticsSnapshot model
│
├── schemas/
│   ├── __init__.py
│   ├── user.py                      # Pydantic: UserCreate, UserResponse, Token
│   ├── course.py                    # CourseCreate, MaterialUpload
│   ├── problem_set.py               # ProblemSetGenerate, ProblemSetResponse
│   ├── submission.py                # SubmissionCreate, GradeResponse
│   └── analytics.py                 # AnalyticsDashboard, GradeDistribution
│
├── services/
│   ├── __init__.py
│   ├── material_service.py          # PDF upload, chunking, RAG ingestion
│   ├── problem_set_service.py       # Generation, PDF export
│   ├── grading_service.py           # Async grading queue, feedback
│   ├── analytics_service.py         # Compute stats, common mistakes
│   └── rag_service.py               # Vector search, chatbot responses
│
├── tasks/
│   ├── __init__.py
│   └── background_tasks.py          # Celery tasks (chunking, grading)
│
├── utils/
│   ├── __init__.py
│   ├── pdf_utils.py                 # PDF extraction, OCR
│   └── progress_tracker.py          # WebSocket progress updates
│
├── agent_orchestrator.py            # (existing) AI agents
├── grading_agents.py                # (existing) Grading agents
├── vector_store.py                  # (existing) ChromaDB wrapper
├── chunker.py                       # (existing) Document chunking
├── pdf_extractor.py                 # (existing) PDF text extraction
├── alembic/                         # Database migrations
│   ├── versions/
│   └── env.py
├── tests/
│   ├── test_auth.py
│   ├── test_professor.py
│   ├── test_student.py
│   └── test_grading.py
├── .env.example
├── requirements.txt
├── alembic.ini
└── main.py                          # Application entry point
```

---

## Data Models

### Database Models (PostgreSQL)

```python
# models/user.py
class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    role = Column(Enum(UserRole), nullable=False)  # PROFESSOR, STUDENT
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    courses_taught = relationship("Course", back_populates="professor")
    enrollments = relationship("Enrollment", back_populates="student")
    submissions = relationship("Submission", back_populates="student")

class UserRole(str, Enum):
    PROFESSOR = "professor"
    STUDENT = "student"


# models/course.py
class Course(Base):
    __tablename__ = "courses"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    code = Column(String, unique=True, nullable=False)  # e.g., "INDE301"
    name = Column(String, nullable=False)
    professor_id = Column(UUID, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    professor = relationship("User", back_populates="courses_taught")
    materials = relationship("CourseMaterial", back_populates="course")
    problem_sets = relationship("ProblemSet", back_populates="course")
    enrollments = relationship("Enrollment", back_populates="course")

class CourseMaterial(Base):
    __tablename__ = "course_materials"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    course_id = Column(UUID, ForeignKey("courses.id"), nullable=False)
    title = Column(String, nullable=False)
    doc_id = Column(String, unique=True, nullable=False)  # ChromaDB doc_id
    file_path = Column(String)  # S3 or local path to original PDF
    chunk_count = Column(Integer, default=0)
    processing_status = Column(Enum(ProcessingStatus), default=ProcessingStatus.PENDING)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    course = relationship("Course", back_populates="materials")

class ProcessingStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class Enrollment(Base):
    __tablename__ = "enrollments"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID, ForeignKey("users.id"), nullable=False)
    course_id = Column(UUID, ForeignKey("courses.id"), nullable=False)
    enrolled_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    student = relationship("User", back_populates="enrollments")
    course = relationship("Course", back_populates="enrollments")
    
    __table_args__ = (UniqueConstraint('student_id', 'course_id'),)


# models/problem_set.py
class ProblemSet(Base):
    __tablename__ = "problem_sets"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    course_id = Column(UUID, ForeignKey("courses.id"), nullable=False)
    doc_id = Column(String, nullable=False)  # Source material doc_id
    title = Column(String, nullable=False)
    num_problems = Column(Integer, nullable=False)
    data = Column(JSONB)  # Full problem set JSON
    pdf_path = Column(String)  # Path to generated PDF
    is_published = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    due_date = Column(DateTime(timezone=True))
    
    # Relationships
    course = relationship("Course", back_populates="problem_sets")
    submissions = relationship("Submission", back_populates="problem_set")


# models/submission.py
class Submission(Base):
    __tablename__ = "submissions"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    problem_set_id = Column(UUID, ForeignKey("problem_sets.id"), nullable=False)
    student_id = Column(UUID, ForeignKey("users.id"), nullable=False)
    problem_number = Column(Integer, nullable=False)
    file_path = Column(String)  # Path to submitted PDF
    extracted_text = Column(Text)  # OCR-extracted content
    submission_status = Column(Enum(SubmissionStatus), default=SubmissionStatus.PENDING)
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    problem_set = relationship("ProblemSet", back_populates="submissions")
    student = relationship("User", back_populates="submissions")
    grade = relationship("Grade", back_populates="submission", uselist=False)
    
    __table_args__ = (UniqueConstraint('problem_set_id', 'student_id', 'problem_number'),)

class SubmissionStatus(str, Enum):
    PENDING = "pending"
    GRADING = "grading"
    GRADED = "graded"
    FAILED = "failed"

class Grade(Base):
    __tablename__ = "grades"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    submission_id = Column(UUID, ForeignKey("submissions.id"), nullable=False, unique=True)
    score = Column(Float, nullable=False)
    max_score = Column(Float, nullable=False)
    percentage = Column(Float, nullable=False)
    letter_grade = Column(String(2))
    rubric = Column(JSONB)  # Detailed rubric breakdown
    feedback = Column(Text)  # Personalized feedback
    evaluation = Column(JSONB)  # Full evaluation JSON
    graded_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    submission = relationship("Submission", back_populates="grade")


# models/analytics.py
class AnalyticsSnapshot(Base):
    __tablename__ = "analytics_snapshots"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    course_id = Column(UUID, ForeignKey("courses.id"), nullable=False)
    problem_set_id = Column(UUID, ForeignKey("problem_sets.id"))
    snapshot_date = Column(DateTime(timezone=True), server_default=func.now())
    
    # Metrics
    total_submissions = Column(Integer)
    average_score = Column(Float)
    median_score = Column(Float)
    grade_distribution = Column(JSONB)  # {"A": 5, "B": 10, ...}
    common_mistakes = Column(JSONB)  # Top 5 errors across students
    completion_rate = Column(Float)
```

### Pydantic Schemas (API Request/Response)

```python
# schemas/user.py
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    role: UserRole

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: UUID
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# schemas/course.py
class CourseCreate(BaseModel):
    code: str
    name: str

class CourseResponse(BaseModel):
    id: UUID
    code: str
    name: str
    professor_id: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True

class MaterialUploadResponse(BaseModel):
    id: UUID
    title: str
    doc_id: str
    chunk_count: int
    processing_status: ProcessingStatus
    
    class Config:
        from_attributes = True


# schemas/problem_set.py
class ProblemSetGenerate(BaseModel):
    doc_id: str
    num_problems: int = 5
    check_quality: bool = True
    due_date: Optional[datetime] = None

class ProblemSetResponse(BaseModel):
    id: UUID
    title: str
    doc_id: str
    num_problems: int
    is_published: bool
    pdf_url: Optional[str] = None
    due_date: Optional[datetime] = None
    created_at: datetime
    data: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True


# schemas/submission.py
class SubmissionCreate(BaseModel):
    problem_set_id: UUID
    problem_number: int
    # File uploaded separately via multipart/form-data

class SubmissionResponse(BaseModel):
    id: UUID
    problem_set_id: UUID
    problem_number: int
    submission_status: SubmissionStatus
    submitted_at: datetime
    
    class Config:
        from_attributes = True

class GradeResponse(BaseModel):
    score: float
    max_score: float
    percentage: float
    letter_grade: str
    feedback: str
    rubric: Dict[str, Any]
    graded_at: datetime
    
    class Config:
        from_attributes = True


# schemas/analytics.py
class GradeDistribution(BaseModel):
    A: int = 0
    A_minus: int = 0
    B_plus: int = 0
    B: int = 0
    B_minus: int = 0
    C_plus: int = 0
    C: int = 0
    C_minus: int = 0
    D_plus: int = 0
    D: int = 0
    D_minus: int = 0
    F: int = 0

class CommonMistake(BaseModel):
    category: str  # "Conceptual Error", "Calculation Error", etc.
    description: str
    frequency: int
    example_student_work: Optional[str] = None

class AnalyticsDashboard(BaseModel):
    course_id: UUID
    problem_set_id: Optional[UUID] = None
    total_students: int
    total_submissions: int
    completion_rate: float
    average_score: float
    median_score: float
    min_score: float
    max_score: float
    grade_distribution: GradeDistribution
    common_mistakes: List[CommonMistake]
    generated_at: datetime
```

---

## API Endpoints

### Authentication (Public)

```
POST   /api/auth/register           # Create new user account
POST   /api/auth/login              # Get JWT token
POST   /api/auth/refresh            # Refresh expired token
GET    /api/auth/me                 # Get current user info
```

### Professor Routes (`/api/professor`)

```
# Course Management
POST   /api/professor/courses                     # Create course
GET    /api/professor/courses                     # List my courses
GET    /api/professor/courses/{course_id}         # Get course details
POST   /api/professor/courses/{course_id}/enroll  # Enroll students (bulk)

# Material Management
POST   /api/professor/courses/{course_id}/materials           # Upload PDF material
GET    /api/professor/courses/{course_id}/materials           # List materials
GET    /api/professor/materials/{material_id}/chunks          # View chunks
GET    /api/professor/materials/{material_id}/progress        # Upload progress (SSE)
DELETE /api/professor/materials/{material_id}                 # Delete material

# Problem Set Generation
POST   /api/professor/courses/{course_id}/problem-sets        # Generate problem set
GET    /api/professor/courses/{course_id}/problem-sets        # List problem sets
GET    /api/professor/problem-sets/{ps_id}                    # Get problem set details
GET    /api/professor/problem-sets/{ps_id}/pdf                # Download PDF
PATCH  /api/professor/problem-sets/{ps_id}/publish            # Publish to students
DELETE /api/professor/problem-sets/{ps_id}                    # Delete problem set

# Submission & Grading
GET    /api/professor/problem-sets/{ps_id}/submissions        # View all submissions
GET    /api/professor/submissions/{submission_id}             # Get single submission
POST   /api/professor/submissions/{submission_id}/grade       # Trigger AI grading
POST   /api/professor/problem-sets/{ps_id}/grade-all          # Grade all submissions

# Analytics
GET    /api/professor/courses/{course_id}/analytics           # Course-wide analytics
GET    /api/professor/problem-sets/{ps_id}/analytics          # Problem set analytics
GET    /api/professor/courses/{course_id}/export-grades       # Export CSV
```

### Student Routes (`/api/student`)

```
# Course Access
GET    /api/student/courses                       # List enrolled courses
GET    /api/student/courses/{course_id}           # Get course details

# Materials & RAG
GET    /api/student/courses/{course_id}/materials # Browse materials
POST   /api/student/rag/query                     # Ask chatbot question

# Problem Sets
GET    /api/student/courses/{course_id}/problem-sets     # List published problem sets
GET    /api/student/problem-sets/{ps_id}                 # Get problem set details
GET    /api/student/problem-sets/{ps_id}/pdf             # Download PDF

# Submissions
POST   /api/student/problem-sets/{ps_id}/submit          # Submit solution (PDF upload)
GET    /api/student/submissions                          # List my submissions
GET    /api/student/submissions/{submission_id}          # Get submission details
GET    /api/student/submissions/{submission_id}/grade    # View grade & feedback
```

### Shared Routes (`/api/shared`)

```
# RAG Query (accessible to both roles)
POST   /api/shared/rag/query                      # Contextual Q&A

# Document Access (permission-based)
GET    /api/shared/documents/{doc_id}/chunks      # View chunks (if enrolled)
```

---

## Security Design

### Authentication Flow

```
1. User registers → POST /api/auth/register
   - Password hashed with bcrypt
   - User stored in PostgreSQL
   
2. User logs in → POST /api/auth/login
   - Validate credentials
   - Generate JWT token (expires in 24h)
   - Return access_token + user info
   
3. Authenticated requests
   - Client sends: Authorization: Bearer <token>
   - FastAPI dependency extracts & validates token
   - Injects current_user into route handler
```

### JWT Token Structure

```python
{
  "sub": "user_id",           # Subject (user UUID)
  "email": "prof@university.edu",
  "role": "professor",
  "exp": 1700000000,          # Expiration timestamp
  "iat": 1699913600           # Issued at
}
```

### Role-Based Access Control (RBAC)

```python
# core/security.py

def require_role(allowed_roles: List[UserRole]):
    """Dependency to enforce role-based access."""
    def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail="Insufficient permissions"
            )
        return current_user
    return role_checker

# Usage in routes:
@app.post("/api/professor/courses")
def create_course(
    course: CourseCreate,
    current_user: User = Depends(require_role([UserRole.PROFESSOR]))
):
    # Only professors can create courses
    pass
```

### Resource-Level Permissions

```python
def verify_course_access(course_id: UUID, current_user: User, db: Session):
    """Verify user has access to a specific course."""
    if current_user.role == UserRole.PROFESSOR:
        # Professor must own the course
        course = db.query(Course).filter(
            Course.id == course_id,
            Course.professor_id == current_user.id
        ).first()
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")
    
    elif current_user.role == UserRole.STUDENT:
        # Student must be enrolled
        enrollment = db.query(Enrollment).filter(
            Enrollment.course_id == course_id,
            Enrollment.student_id == current_user.id
        ).first()
        if not enrollment:
            raise HTTPException(status_code=403, detail="Not enrolled in course")
    
    return course
```

### Data Isolation

- **Professors**: Can only access their own courses, materials, and students
- **Students**: Can only access courses they're enrolled in
- **Submissions**: Students see only their own; professors see all in their courses
- **ChromaDB**: Filter queries by `doc_id` to prevent cross-course leakage

---

## Workflows

### 1. Professor Upload Material Workflow

```
┌─────────────┐
│ 1. Upload   │ POST /api/professor/courses/{id}/materials
│    PDF      │ - Multipart/form-data with file
└──────┬──────┘
       │
       v
┌─────────────┐
│ 2. Save     │ - Store PDF in file system/S3
│    File     │ - Create CourseMaterial record (status=PENDING)
└──────┬──────┘
       │
       v
┌─────────────┐
│ 3. Queue    │ - Celery task: process_material_task(material_id)
│    Job      │ - Return material_id to client immediately
└──────┬──────┘
       │
       v (async)
┌─────────────┐
│ 4. Extract  │ - extract_pdf_text() or OCR if needed
│    Text     │ - Update status=PROCESSING
└──────┬──────┘
       │
       v
┌─────────────┐
│ 5. Chunk    │ - chunker.chunk_with_splitting(text)
│    Content  │ - Store in ChromaDB with doc_id
└──────┬──────┘
       │
       v
┌─────────────┐
│ 6. Update   │ - Set chunk_count, status=COMPLETED
│    Record   │ - Notify via WebSocket (optional)
└─────────────┘

Frontend polls: GET /api/professor/materials/{id}/progress
Or uses Server-Sent Events for real-time updates
```

### 2. Professor Generate Problem Set Workflow

```
┌─────────────┐
│ 1. Select   │ POST /api/professor/courses/{id}/problem-sets
│    Material │ Body: {doc_id, num_problems, due_date}
└──────┬──────┘
       │
       v
┌─────────────┐
│ 2. Generate │ - ProblemSetOrchestrator.generate_problem_set()
│    Problems │ - Uses RAG to retrieve relevant chunks
└──────┬──────┘ - Agents generate problems + solutions
       │
       v
┌─────────────┐
│ 3. Save     │ - Create ProblemSet record (is_published=False)
│    to DB    │ - Store full JSON in data field
└──────┬──────┘
       │
       v
┌─────────────┐
│ 4. Generate │ - build_markdown_problems_only() for students
│    PDFs     │ - build_markdown() with solutions for professor
└──────┬──────┘ - pandoc → PDF, save to file system
       │
       v
┌─────────────┐
│ 5. Return   │ - Return ProblemSetResponse
│    Response │ - PDF accessible via /problem-sets/{id}/pdf
└─────────────┘

Professor reviews, then: PATCH /api/professor/problem-sets/{id}/publish
```

### 3. Student Submit & Grade Workflow

```
┌─────────────┐
│ 1. Download │ GET /api/student/problem-sets/{id}/pdf
│    Problem  │ - Get problems-only PDF
└──────┬──────┘
       │
       v
┌─────────────┐
│ 2. Solve    │ - Student works offline
│    Problems │ - Writes/types solution
└──────┬──────┘
       │
       v
┌─────────────┐
│ 3. Submit   │ POST /api/student/problem-sets/{id}/submit
│    PDF      │ - Upload PDF with solution
└──────┬──────┘ - File: multipart/form-data
       │         - problem_number: 1
       v
┌─────────────┐
│ 4. Extract  │ - extract_pdf_smart() (tries text, then OCR)
│    Text     │ - Store Submission (status=PENDING)
└──────┬──────┘
       │
       v
┌─────────────┐
│ 5. Queue    │ - Celery task: grade_submission_task(submission_id)
│    Grading  │ - Update status=GRADING
└──────┬──────┘
       │
       v (async)
┌─────────────┐
│ 6. AI Grade │ - GradingOrchestrator.grade_submission()
│             │ - Generate rubric, evaluate, feedback
└──────┬──────┘
       │
       v
┌─────────────┐
│ 7. Save     │ - Create Grade record
│    Results  │ - Update status=GRADED
└──────┬──────┘ - Notify student (email/notification)
       │
       v
┌─────────────┐
│ 8. View     │ GET /api/student/submissions/{id}/grade
│    Feedback │ - Student sees score + detailed feedback
└─────────────┘
```

### 4. Professor Analytics Dashboard Workflow

```
┌─────────────┐
│ 1. Request  │ GET /api/professor/problem-sets/{id}/analytics
│    Analytics│
└──────┬──────┘
       │
       v
┌─────────────┐
│ 2. Query    │ - Fetch all graded submissions for problem set
│    Grades   │ - Calculate: avg, median, min, max, distribution
└──────┬──────┘
       │
       v
┌─────────────┐
│ 3. Analyze  │ - Extract common errors from evaluations
│    Mistakes │ - Use LLM to categorize (Conceptual, Calculation, etc.)
└──────┬──────┘ - Rank by frequency
       │
       v
┌─────────────┐
│ 4. Cache    │ - Store AnalyticsSnapshot for performance
│    Results  │ - Invalidate when new submissions graded
└──────┬──────┘
       │
       v
┌─────────────┐
│ 5. Return   │ - AnalyticsDashboard schema
│    Dashboard│ - Charts data ready for frontend
└─────────────┘
```

---

## Database Schema

### Entity Relationship Diagram

```
┌─────────────┐         ┌──────────────┐
│    User     │◄────────│   Course     │
│ (Student/   │         │              │
│  Professor) │         └──────┬───────┘
└──────┬──────┘                │
       │                       │
       │ enrolls in    teaches │
       │                       │
       v                       v
┌─────────────┐         ┌──────────────┐
│ Enrollment  │         │Course        │
└─────────────┘         │Material      │
                        └──────┬───────┘
                               │
                        has    │
                               v
                        ┌──────────────┐
                        │ ProblemSet   │
                        └──────┬───────┘
                               │
                        has    │
                               v
                        ┌──────────────┐
                        │ Submission   │
                        └──────┬───────┘
                               │
                        has    │
                               v
                        ┌──────────────┐
                        │    Grade     │
                        └──────────────┘
```

### Key Indexes

```sql
-- Performance-critical indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);

CREATE INDEX idx_courses_professor ON courses(professor_id);
CREATE INDEX idx_materials_course ON course_materials(course_id);
CREATE INDEX idx_materials_docid ON course_materials(doc_id);

CREATE INDEX idx_enrollments_student ON enrollments(student_id);
CREATE INDEX idx_enrollments_course ON enrollments(course_id);

CREATE INDEX idx_problemsets_course ON problem_sets(course_id);
CREATE INDEX idx_problemsets_published ON problem_sets(is_published);

CREATE INDEX idx_submissions_problemset ON submissions(problem_set_id);
CREATE INDEX idx_submissions_student ON submissions(student_id);
CREATE INDEX idx_submissions_status ON submissions(submission_status);

CREATE INDEX idx_grades_submission ON grades(submission_id);
```

---

## Implementation Roadmap

### Phase 1: Core Infrastructure (Week 1)
- [ ] Setup FastAPI project structure
- [ ] Implement JWT authentication
- [ ] Create database models with SQLAlchemy
- [ ] Setup Alembic migrations
- [ ] Implement RBAC dependencies

### Phase 2: Professor Features (Week 2)
- [ ] Material upload with chunking
- [ ] Background task processing (Celery)
- [ ] Progress tracking (WebSocket/SSE)
- [ ] Problem set generation API
- [ ] PDF export functionality

### Phase 3: Student Features (Week 3)
- [ ] Course enrollment
- [ ] RAG chatbot endpoint
- [ ] Problem set viewing
- [ ] Submission upload with OCR
- [ ] Grade viewing

### Phase 4: Grading System (Week 4)
- [ ] Async grading queue
- [ ] Batch grading endpoint
- [ ] Analytics computation
- [ ] Common mistake extraction
- [ ] Dashboard API

### Phase 5: Testing & Optimization (Week 5)
- [ ] Unit tests (pytest)
- [ ] Integration tests
- [ ] Load testing
- [ ] Query optimization
- [ ] Caching strategy

---

## Configuration Example

```python
# core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Application
    APP_NAME: str = "University LMS"
    API_V1_PREFIX: str = "/api"
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str
    
    # Security
    SECRET_KEY: str  # For JWT signing
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    
    # OpenAI
    OPENAI_API_KEY: str
    
    # Vector Store
    CHROMA_PERSIST_DIRECTORY: str = "./rag_db"
    
    # File Storage
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024  # 50MB
    
    # Celery (for background tasks)
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    
    # CORS
    ALLOWED_ORIGINS: list = ["http://localhost:3000"]
    
    class Config:
        env_file = ".env"

settings = Settings()
```

---

## Next Steps

1. **Implement authentication routes** in `api/routes/auth.py`
2. **Create database models** with proper relationships
3. **Setup Alembic** for database migrations
4. **Implement background tasks** using Celery for long-running operations
5. **Add WebSocket/SSE** for real-time progress updates
6. **Build analytics service** for common mistake extraction
7. **Add rate limiting** to prevent abuse
8. **Implement caching** (Redis) for frequently accessed data
9. **Setup logging** for debugging and monitoring
10. **Write comprehensive tests**

This architecture provides a solid foundation for a production-ready LMS with proper separation of concerns, security, and scalability.
