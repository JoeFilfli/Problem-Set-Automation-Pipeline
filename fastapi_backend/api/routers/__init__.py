"""
Router __init__ file to export all routers.
"""
from api.routers.materials import router as materials_router
from api.routers.problem_sets import router as problem_sets_router
from api.routers.submissions import router as submissions_router
from api.routers.rag import router as rag_router
from api.routers.mcqs import router as mcqs_router
from api.routers.analytics import router as analytics_router
from api.routers.images import router as images_router

__all__ = [
    "materials_router",
    "problem_sets_router",
    "submissions_router",
    "rag_router",
    "mcqs_router",
    "analytics_router",
    "images_router",
]
