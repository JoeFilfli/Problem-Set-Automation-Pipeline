# Quick Start Script for Problem-Set Automation Pipeline (Windows)
# This script helps you get up and running with Docker quickly

Write-Host "===================================" -ForegroundColor Cyan
Write-Host "Problem-Set Automation Pipeline" -ForegroundColor Cyan
Write-Host "Docker Quick Start Script" -ForegroundColor Cyan
Write-Host "===================================" -ForegroundColor Cyan
Write-Host ""

# Check if Docker is installed
try {
    docker --version | Out-Null
    Write-Host "✅ Docker is installed" -ForegroundColor Green
} catch {
    Write-Host "❌ Error: Docker is not installed" -ForegroundColor Red
    Write-Host "Please install Docker Desktop from: https://www.docker.com/products/docker-desktop/" -ForegroundColor Yellow
    exit 1
}

# Check if Docker Compose is installed
try {
    docker-compose --version | Out-Null
    Write-Host "✅ Docker Compose is installed" -ForegroundColor Green
} catch {
    Write-Host "❌ Error: Docker Compose is not installed" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Check if .env file exists
if (-not (Test-Path "fastapi_backend\.env")) {
    Write-Host "⚠️  No .env file found" -ForegroundColor Yellow
    Write-Host "Creating .env file from example..." -ForegroundColor Yellow
    
    if (Test-Path "fastapi_backend\.env.example") {
        Copy-Item "fastapi_backend\.env.example" "fastapi_backend\.env"
        Write-Host "✅ Created fastapi_backend\.env" -ForegroundColor Green
        Write-Host ""
        Write-Host "⚠️  IMPORTANT: You need to add your OpenAI API key!" -ForegroundColor Yellow
        Write-Host "Edit fastapi_backend\.env and add your API key:" -ForegroundColor Yellow
        Write-Host "  OPENAI_API_KEY=your_key_here" -ForegroundColor Cyan
        Write-Host ""
        
        # Open the file in notepad
        $response = Read-Host "Would you like to open the .env file now? (y/n)"
        if ($response -eq "y" -or $response -eq "Y") {
            notepad "fastapi_backend\.env"
            Read-Host "Press Enter after you've saved the file with your API key..."
        } else {
            Read-Host "Press Enter after you've manually added your API key..."
        }
    } else {
        Write-Host "❌ Error: .env.example file not found" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "✅ Found .env file" -ForegroundColor Green
}

# Check if API key is set
$envContent = Get-Content "fastapi_backend\.env" -Raw
if ($envContent -match "your_openai_api_key_here") {
    Write-Host ""
    Write-Host "⚠️  WARNING: Default API key detected" -ForegroundColor Yellow
    Write-Host "Please edit fastapi_backend\.env and add your real OpenAI API key" -ForegroundColor Yellow
    Write-Host ""
    $response = Read-Host "Press Enter to continue anyway, or Ctrl+C to exit"
}

Write-Host ""
Write-Host "===================================" -ForegroundColor Cyan
Write-Host "Starting Docker containers..." -ForegroundColor Cyan
Write-Host "===================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "This may take a few minutes on first run..." -ForegroundColor Yellow
Write-Host ""

# Build and start containers
docker-compose up --build -d

Write-Host ""
Write-Host "===================================" -ForegroundColor Cyan
Write-Host "✅ Application started successfully!" -ForegroundColor Green
Write-Host "===================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Access the application at:" -ForegroundColor White
Write-Host "  Frontend:  http://localhost:3000" -ForegroundColor Cyan
Write-Host "  Backend:   http://localhost:8000" -ForegroundColor Cyan
Write-Host "  API Docs:  http://localhost:8000/api/py/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "Useful commands:" -ForegroundColor White
Write-Host "  View logs:        docker-compose logs -f" -ForegroundColor Gray
Write-Host "  Stop containers:  docker-compose down" -ForegroundColor Gray
Write-Host "  Restart:          docker-compose restart" -ForegroundColor Gray
Write-Host ""
Write-Host "For detailed documentation, see DOCKER.md" -ForegroundColor Yellow
Write-Host ""

# Ask if user wants to view logs
$response = Read-Host "Would you like to view the logs now? (y/n)"
if ($response -eq "y" -or $response -eq "Y") {
    Write-Host "Showing logs (press Ctrl+C to exit)..." -ForegroundColor Yellow
    docker-compose logs -f
}

