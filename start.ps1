# ========================================================
# Start AI Voice Calling Agent (LiveKit WebRTC + Python)
# ========================================================

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " 🚀 AI Voice Calling Agent (LiveKit WebRTC & Python) " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# Check Python installation
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "Error: Python 3.10+ is required but not found in PATH." -ForegroundColor Red
    exit 1
}

# Create virtual environment if missing
if (-not (Test-Path "venv")) {
    Write-Host "Creating Python virtual environment in .\venv..." -ForegroundColor Yellow
    python -m venv venv
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Green
& ".\venv\Scripts\Activate.ps1"

# Install/Update dependencies
Write-Host "Checking dependencies from requirements.txt..." -ForegroundColor Yellow
pip install -r requirements.txt

Write-Host "`nSelect Mode to Run:" -ForegroundColor Cyan
Write-Host " [1] Start LiveKit WebRTC Agent Worker (Real-time Audio Engine)" -ForegroundColor Yellow
Write-Host " [2] Start FastAPI Backend & Token Server (Port 8000)" -ForegroundColor Yellow
Write-Host " [3] Start Both in separate windows" -ForegroundColor Yellow

$choice = Read-Host "`nEnter Choice [1, 2, or 3] (Default: 3)"

if ($choice -eq "1") {
    Write-Host "`n🎙️ Starting LiveKit Voice Agent Worker..." -ForegroundColor Green
    python app/livekit_agent/agent.py dev
} elseif ($choice -eq "2") {
    Write-Host "`n🚀 Starting FastAPI REST & Token Server on http://localhost:8000..." -ForegroundColor Green
    python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
} else {
    Write-Host "`n🚀 Launching FastAPI Backend & LiveKit WebRTC Worker together..." -ForegroundColor Green
    python run.py
}
