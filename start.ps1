$ErrorActionPreference = "Stop"

$projectRoot = $PSScriptRoot
$backendPath = Join-Path $projectRoot "backend"
$frontendPath = Join-Path $projectRoot "frontend"
$pythonPath = Join-Path $projectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $pythonPath)) {
    $pythonPath = "python"
}

if (-not (Test-Path (Join-Path $frontendPath "node_modules"))) {
    Write-Host "Frontend dependencies are missing. Run: cd frontend; npm install" -ForegroundColor Yellow
    exit 1
}

Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "Set-Location '$projectRoot'; & '$pythonPath' -m uvicorn app.main:app --app-dir backend --reload --host 127.0.0.1 --port 8000"
)

Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "Set-Location '$frontendPath'; npm run dev"
)

Write-Host "Backend:  http://localhost:8000/docs" -ForegroundColor Green
Write-Host "Frontend: http://localhost:5173" -ForegroundColor Green