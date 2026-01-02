# Running the App with Docker

## Prerequisites

- [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/)
- Make sure Docker Desktop is running

## Setup Instructions

### 1. Create Environment Variables File

Copy the example environment file and fill in your values: 

```powershell
Copy-Item .env.example .env
```

Then edit `.env` with your favorite text editor (Notepad, VS Code, etc.) and fill in: 
- `ADMIN_PASS`: Your admin password
- Database credentials if you're using Neon (or set `USE_NEON=false` to use JSON file storage)

### 2. Run the Application

You have several options:

#### Option A: Using PowerShell Script (Easiest)
```powershell
.\run-app.ps1
```

#### Option B: Using Docker Compose Directly
```powershell
# Build and run in foreground (see logs)
docker-compose up --build

# Or run in background (detached mode)
docker-compose up -d --build
```

### 3. Access the Application

Once running, open your browser and go to:
```
http://localhost:8501
```

### 4. Stop the Application

#### If running in foreground:
Press `Ctrl + C`

#### If running in background: 
```powershell
docker-compose down
```

## Common Commands

```powershell
# Start the app
docker-compose up -d

# Stop the app
docker-compose down

# View logs
docker-compose logs -f

# Rebuild after code changes
docker-compose up --build -d

# Remove everything (including volumes)
docker-compose down -v
```

## Troubleshooting

### Port 8501 already in use
Stop any other Streamlit apps or change the port in `docker-compose.yml`:
```yaml
ports:
  - "8502:8501"  # Use 8502 instead
```

### Database connection issues
If using Neon database:
1. Verify your `.env` file has correct credentials
2. Check that `USE_NEON=true`
3. Ensure your Neon database is accessible

### Data persistence
- **JSON mode**: Data is stored in `./data/data.json` on your host machine
- **Neon mode**:  Data is stored in your Neon PostgreSQL database

## Switching Between JSON and Neon

Simply change the `USE_NEON` variable in your `.env` file: 

```env
# Use JSON file
USE_NEON=false

# Use Neon database
USE_NEON=true
```

Then restart the container:
```powershell
docker-compose restart
```