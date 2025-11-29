#!/bin/bash

# Quick Start Script for Problem-Set Automation Pipeline
# This script helps you get up and running with Docker quickly

set -e  # Exit on error

echo "==================================="
echo "Problem-Set Automation Pipeline"
echo "Docker Quick Start Script"
echo "==================================="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Error: Docker is not installed"
    echo "Please install Docker Desktop from: https://www.docker.com/products/docker-desktop/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Error: Docker Compose is not installed"
    echo "Please install Docker Compose"
    exit 1
fi

echo "✅ Docker is installed"
echo "✅ Docker Compose is installed"
echo ""

# Check if .env file exists
if [ ! -f "fastapi_backend/.env" ]; then
    echo "⚠️  No .env file found"
    echo "Creating .env file from example..."
    
    if [ -f "fastapi_backend/.env.example" ]; then
        cp fastapi_backend/.env.example fastapi_backend/.env
        echo "✅ Created fastapi_backend/.env"
        echo ""
        echo "⚠️  IMPORTANT: You need to add your OpenAI API key!"
        echo "Edit fastapi_backend/.env and add your API key:"
        echo "  OPENAI_API_KEY=your_key_here"
        echo ""
        read -p "Press Enter after you've added your API key..."
    else
        echo "❌ Error: .env.example file not found"
        exit 1
    fi
else
    echo "✅ Found .env file"
fi

# Check if API key is set
if grep -q "your_openai_api_key_here" fastapi_backend/.env; then
    echo ""
    echo "⚠️  WARNING: Default API key detected"
    echo "Please edit fastapi_backend/.env and add your real OpenAI API key"
    echo ""
    read -p "Press Enter to continue anyway, or Ctrl+C to exit..."
fi

echo ""
echo "==================================="
echo "Starting Docker containers..."
echo "==================================="
echo ""
echo "Building and starting services..."
echo "This may take a few minutes on first run..."
echo ""

# Build and start containers
docker-compose up --build -d

echo ""
echo "==================================="
echo "✅ Application started successfully!"
echo "==================================="
echo ""
echo "Access the application at:"
echo "  Frontend:  http://localhost:3000"
echo "  Backend:   http://localhost:8000"
echo "  API Docs:  http://localhost:8000/api/py/docs"
echo ""
echo "Useful commands:"
echo "  View logs:        docker-compose logs -f"
echo "  Stop containers:  docker-compose down"
echo "  Restart:          docker-compose restart"
echo ""
echo "For detailed documentation, see DOCKER.md"
echo ""

# Ask if user wants to view logs
read -p "Would you like to view the logs now? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Showing logs (press Ctrl+C to exit)..."
    docker-compose logs -f
fi

