# Setup Instructions

## Prerequisites

### Option 1: With Docker (Recommended for Full Gateway Experience)
- **Docker Desktop** (includes Docker Compose)
  - Mac: Download from https://www.docker.com/products/docker-desktop
  - After installation, verify with: `docker --version`

### Option 2: Without Docker (Local Development Only)
- Python 3.12+
- NGINX (install separately)
- This allows testing the backend but not the full API Gateway features

## Installation

### Full Setup with Docker (Recommended)

1. **Install Docker Desktop**
   - Download and install Docker Desktop for Mac
   - Start Docker Desktop application
   - Verify: `docker --version` and `docker compose version`

2. **Start the Gateway**
   ```bash
   # Build and start all services (NGINX + 3 backend instances)
   docker compose up --build -d
   
   # Check status
   docker compose ps
   ```

3. **Verify Gateway is Running**
   ```bash
   # Check gateway status
   curl http://localhost:8080/gateway/status
   
   # Check backend health
   curl http://localhost:8080/healthz
   ```

4. **Run Validation Tests**
   ```bash
   # Python validation (comprehensive)
   python3 validate_gateway.py
   
   # Bash demo (interactive)
   ./demo_gateway.sh
   
   # Or use Make commands
   make validate
   make demo
   ```

### Local Development without Docker

If Docker is not available, you can still run the backend service locally:

1. **Install Dependencies**
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Run Single Backend Instance**
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

3. **Test Backend Directly** (No API Gateway features)
   ```bash
   # Health check (no API key needed)
   curl http://localhost:8000/healthz
   
   # Price calculation (no API key needed without gateway)
   curl -X POST http://localhost:8000/v1/price \
     -H "Content-Type: application/json" \
     -d '{"base_price": 100, "discount_code": "WELCOME10"}'
   ```

**Note**: Without Docker, you won't have:
- NGINX API Gateway
- Rate limiting
- Load balancing
- Caching
- API key authentication
- Multiple backend instances

### Setting up NGINX Locally (Advanced)

If you want to test NGINX features without Docker:

1. **Install NGINX**
   ```bash
   # Mac with Homebrew
   brew install nginx
   ```

2. **Configure NGINX**
   ```bash
   # Copy our nginx.conf to NGINX config directory
   # Update the upstream servers to point to localhost:8000
   # (Remove host.docker.internal references)
   ```

3. **Start Services**
   ```bash
   # Terminal 1: Start backend
   uvicorn app.main:app --port 8000
   
   # Terminal 2: Start NGINX
   nginx -c /path/to/nginx.conf
   ```

This is more complex and we recommend using Docker instead.

## Troubleshooting

### Docker Issues

**Problem**: `docker: command not found`
- **Solution**: Install Docker Desktop from https://www.docker.com/products/docker-desktop

**Problem**: `Cannot connect to the Docker daemon`
- **Solution**: Start Docker Desktop application

**Problem**: Port 8080 already in use
- **Solution**: Stop other services using port 8080
  ```bash
  lsof -ti :8080 | xargs kill -9
  ```

**Problem**: Port 8000/8001/8002 already in use
- **Solution**: Stop services using these ports
  ```bash
  lsof -ti :8000 :8001 :8002 | xargs kill -9
  docker compose down
  ```

### Python Issues

**Problem**: `ModuleNotFoundError`
- **Solution**: Install dependencies
  ```bash
  pip install -r requirements.txt
  ```

**Problem**: `pydantic.errors.PydanticImportError: BaseSettings`
- **Solution**: Install pydantic-settings
  ```bash
  pip install pydantic-settings
  ```

## Next Steps

### If Docker is Installed
1. Run `docker compose up --build -d`
2. Run `python3 validate_gateway.py`
3. Read `GATEWAY_GUIDE.md` for detailed explanations
4. Try the exercises in the guide

### If Docker is NOT Installed
1. Install Docker Desktop
2. Then follow the steps above
3. Alternatively, explore the backend API at http://localhost:8000/docs

## Quick Reference

### Docker Commands
```bash
# Start services
docker compose up -d

# Stop services
docker compose down

# View logs
docker compose logs -f

# Restart services
docker compose restart

# Check status
docker compose ps
```

### Make Commands (Requires Docker)
```bash
make help          # Show all commands
make up            # Start services
make down          # Stop services
make validate      # Run tests
make demo          # Interactive demo
make logs          # View logs
make clean         # Clean up
```

### Direct Testing (No Docker Required)
```bash
# Start backend
uvicorn app.main:app --reload --port 8000

# Test in another terminal
curl -X POST http://localhost:8000/v1/price \
  -H "Content-Type: application/json" \
  -d '{"base_price": 100}'
```

## Learning Resources

- **GATEWAY_GUIDE.md** - Complete guide to all API Gateway features
- **README.md** - Project overview and quick start
- **nginx.conf** - Annotated NGINX configuration
- **validate_gateway.py** - Test suite with detailed comments
