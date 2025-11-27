"""
FastAPI application entry point.
Includes all routers and core configuration.
"""
from typing import Any, Dict
import json

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI

from api.routers import (
    materials_router,
    problem_sets_router,
    submissions_router,
    rag_router,
    mcqs_router,
    analytics_router,
    images_router,
    guided_solve_router,
    beat_ai_router,
)
from api.dependencies import get_vector_store

# Create FastAPI instance with custom docs and openapi url
app = FastAPI(docs_url="/api/py/docs", openapi_url="/api/py/openapi.json")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routers
app.include_router(materials_router)
app.include_router(problem_sets_router)
app.include_router(submissions_router)
app.include_router(rag_router)
app.include_router(mcqs_router)
app.include_router(analytics_router)
app.include_router(images_router)
app.include_router(guided_solve_router)
app.include_router(beat_ai_router)


# Core endpoints
@app.get("/api/py/helloFastApi")
def hello_fast_api():
    return {"message": "Hello from FastAPI"}


@app.get("/api/py/health")
def health_check() -> Dict[str, Any]:
    """
    Comprehensive health check for the API and its dependencies.
    
    Returns:
        Health status of all system components
    """
    health_status = {
        "api": "healthy",
        "vector_store": "unknown",
        "openai": "unknown"
    }
    
    # Check vector store
    try:
        vs = get_vector_store()
        docs = vs.get_all_documents()
        health_status["vector_store"] = "healthy"
        health_status["vector_store_docs"] = len(docs)
    except Exception as e:
        health_status["vector_store"] = f"unhealthy: {str(e)}"
    
    # Check OpenAI connection
    try:
        client = OpenAI()
        # Simple test call
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "test"}],
            max_tokens=5
        )
        health_status["openai"] = "healthy"
    except Exception as e:
        health_status["openai"] = f"unhealthy: {str(e)}"
    
    # Determine overall status
    overall_healthy = all(
        status == "healthy" or isinstance(status, int)
        for key, status in health_status.items()
        if key != "vector_store_docs"
    )
    
    return {
        "success": overall_healthy,
        "status": "healthy" if overall_healthy else "degraded",
        "components": health_status,
        "timestamp": json.dumps({"time": "now"})  # Simple timestamp
    }
