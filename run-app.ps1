# PowerShell script to run the app with Docker Compose
# This is a convenience script if you prefer not to type the full docker-compose command

Write-Host "Starting Attendance Tracking App..." -ForegroundColor Green

# Check if . env file exists
if (-not (Test-Path ".env")) {
    Write-Host "Warning: .env file not found!" -ForegroundColor Yellow
    Write-Host "Please create a .env file based on .env.example" -ForegroundColor Yellow
    Write-Host ""
    $response = Read-Host "Do you want to continue anyway? (y/n)"
    if ($response -ne "y") {
        exit
    }
}

# Build and start the containers
docker-compose up --build

# Note: Use Ctrl+C to stop the app
# To run in background (detached mode), use: docker-compose up -d --build