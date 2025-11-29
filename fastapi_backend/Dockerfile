# Use Python 3.12 slim image for smaller size
FROM python:3.12-slim

# Set working directory in container
WORKDIR /app

# Set environment variables
# Prevents Python from writing pyc files to disc
ENV PYTHONDONTWRITEBYTECODE=1
# Prevents Python from buffering stdout and stderr
ENV PYTHONUNBUFFERED=1

# Install system dependencies
# These are needed for some Python packages to compile
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
# Use --no-cache-dir to reduce image size
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy all application code
COPY . .

# Create directories for data persistence
# These will store problem sets, submissions, and RAG database
RUN mkdir -p api_storage/problem_sets \
    api_storage/submissions \
    api_storage/saved_mcqs \
    api_storage/beat_ai_challenges \
    api_storage/beat_ai_submissions \
    api_storage/feedback \
    api_storage/images \
    api_storage/exams \
    rag_db \
    sample_materials \
    student_work

# Expose port 8000 for FastAPI
EXPOSE 8000

# Health check to ensure container is running properly
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/api/py/health')" || exit 1

# Run the FastAPI application with uvicorn
# --host 0.0.0.0 makes it accessible from outside the container
# --port 8000 is the standard port for this app
CMD ["uvicorn", "api.index:app", "--host", "0.0.0.0", "--port", "8000"]

