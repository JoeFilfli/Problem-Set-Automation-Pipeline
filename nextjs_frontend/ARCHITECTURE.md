# AUB LMS Architecture

## Directory Structure

```
nextjs_frontend/
├── app/
│   ├── layout.tsx                    # Root layout with AUB theme
│   ├── page.tsx                      # Landing/login page
│   ├── globals.css                   # Global styles + Tailwind
│   │
│   ├── (auth)/                       # Auth route group
│   │   ├── login/
│   │   │   └── page.tsx
│   │   └── register/
│   │       └── page.tsx
│   │
│   ├── professor/                    # Professor route group
│   │   ├── layout.tsx               # Professor-specific layout
│   │   ├── page.tsx                 # Professor dashboard
│   │   ├── materials/
│   │   │   ├── page.tsx            # Upload & manage materials
│   │   │   └── [docId]/
│   │   │       └── page.tsx        # View chunks for specific doc
│   │   ├── problem-sets/
│   │   │   ├── page.tsx            # List all problem sets
│   │   │   ├── generate/
│   │   │   │   └── page.tsx        # Generate new problem set
│   │   │   └── [setId]/
│   │   │       ├── page.tsx        # View problem set
│   │   │       ├── submissions/
│   │   │       │   └── page.tsx    # View submissions
│   │   │       └── grading/
│   │   │           └── page.tsx    # Grade submissions
│   │   └── analytics/
│   │       └── page.tsx             # Analytics dashboard
│   │
│   └── student/                      # Student route group
│       ├── layout.tsx               # Student-specific layout
│       ├── page.tsx                 # Student dashboard
│       ├── workspace/
│       │   └── page.tsx            # 3-column workspace (main interface)
│       ├── problem-sets/
│       │   ├── page.tsx            # List problem sets
│       │   └── [setId]/
│       │       ├── page.tsx        # View & work on problem set
│       │       └── submit/
│       │           └── page.tsx    # Submit solution
│       └── grades/
│           └── page.tsx             # View all grades & feedback
│
├── components/
│   ├── ui/                          # Reusable UI components
│   │   ├── Button.tsx
│   │   ├── Card.tsx
│   │   ├── Input.tsx
│   │   ├── Modal.tsx
│   │   ├── Badge.tsx
│   │   ├── Progress.tsx
│   │   ├── Spinner.tsx
│   │   └── Toast.tsx
│   │
│   ├── layout/                      # Layout components
│   │   ├── Header.tsx
│   │   ├── Sidebar.tsx
│   │   ├── Footer.tsx
│   │   └── Navigation.tsx
│   │
│   ├── professor/                   # Professor-specific components
│   │   ├── MaterialUploader.tsx
│   │   ├── ChunkVisualizer.tsx
│   │   ├── ProblemSetGenerator.tsx
│   │   ├── SubmissionList.tsx
│   │   ├── GradingInterface.tsx
│   │   └── AnalyticsCharts.tsx
│   │
│   └── student/                     # Student-specific components
│       ├── MaterialsPanel.tsx
│       ├── ChatInterface.tsx
│       ├── ProblemSetPanel.tsx
│       ├── SubmissionUploader.tsx
│       └── FeedbackViewer.tsx
│
├── lib/
│   ├── api/                         # API client functions
│   │   ├── client.ts               # Base API client
│   │   ├── materials.ts            # Materials endpoints
│   │   ├── problemSets.ts          # Problem sets endpoints
│   │   ├── grading.ts              # Grading endpoints
│   │   └── rag.ts                  # RAG/chat endpoints
│   │
│   ├── hooks/                       # Custom React hooks
│   │   ├── useAuth.ts
│   │   ├── useMaterials.ts
│   │   ├── useProblemSets.ts
│   │   ├── useGrading.ts
│   │   └── useChat.ts
│   │
│   ├── types/                       # TypeScript types
│   │   ├── api.ts
│   │   ├── user.ts
│   │   ├── material.ts
│   │   ├── problemSet.ts
│   │   └── grading.ts
│   │
│   └── utils/                       # Utility functions
│       ├── formatters.ts
│       ├── validators.ts
│       └── constants.ts
│
├── public/
│   ├── images/
│   │   ├── aub-logo.svg
│   │   └── icons/
│   └── fonts/
│
└── tailwind.config.ts               # Tailwind configuration
```

## Data Flow

### Professor Flow
1. Upload PDF → FastAPI processes → Chunks stored
2. Select material → Generate problem set → AI creates problems
3. Students submit → Professor triggers grading → AI grades
4. View analytics → Charts show performance

### Student Flow
1. Browse materials → Select material → View chunks
2. Chat with AI → RAG retrieves context → AI responds
3. View problem sets → Download/work on problems → Upload solution
4. View grades → See rubric & feedback

## State Management

Using React hooks + SWR for data fetching:
- `useSWR` for GET requests (auto-revalidation)
- `mutate` for optimistic updates
- Local state for UI interactions

## API Integration

Base URL: `http://127.0.0.1:8000` (development)

### Endpoints Used
- GET `/api/py/chapters` - List materials
- POST `/api/py/upload-material` - Upload PDF
- GET `/api/py/documents/{docId}/chunks` - View chunks
- POST `/api/py/generate-problem-set` - Generate problems
- POST `/api/py/rag-query` - Chat with AI
- POST `/api/py/grade-submissions` - Grade submissions
- GET `/api/py/stats` - System statistics

## Authentication

Simple role-based auth:
- Store user role in localStorage/cookie
- Protect routes with middleware
- Redirect based on role

## Performance Optimizations

- Code splitting by route
- Image optimization with Next.js Image
- SWR caching for API calls
- Lazy loading for heavy components
- Debounced search inputs

