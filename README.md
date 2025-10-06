````markdown
# FastAPI Microservice with NGINX API Gateway

A production-ready FastAPI microservice demonstrating API Gateway patterns with NGINX. This project includes:
- **NGINX API Gateway** with rate limiting, caching, load balancing, and authentication
- **FastAPI Backend** with price calculation, VAT, and discount codes
- **Comprehensive validation suite** to test all gateway features
- **Complete learning guide** for understanding API Gateway concepts

## 🚀 Quick Start with API Gateway

### Prerequisites
- Docker & Docker Compose
- Python 3.12+ (for local testing)
- curl or httpx (for testing)

### Start Everything (Recommended)
```bash
# Using Make (easiest)
make up          # Start NGINX + 3 backend instances
make validate    # Run comprehensive tests
make demo        # Interactive feature demo

# Or using Docker Compose directly
docker-compose up -d
python3 validate_gateway.py
```

The API Gateway will be available at **http://localhost:8080**

### Test Features Quickly
```bash
# Test authentication
make test-auth

# Test caching
make test-cache

# Test rate limiting
make test-rate-limit

# Check health
make health
```

## 📚 API Gateway Features

This implementation showcases **10 essential API Gateway features**:

1. **Rate Limiting** - 10 req/s per IP, 100 req/s per API key
2. **Load Balancing** - Distributes traffic across 3 backend instances
3. **Response Caching** - 5-minute cache with stale-while-revalidate
4. **API Key Authentication** - Validates `X-API-Key` header
5. **CORS Configuration** - Proper cross-origin support
6. **Security Headers** - X-Frame-Options, XSS-Protection, etc.
7. **Request Logging** - Structured logs with timing info
8. **Health Checks** - Gateway and backend monitoring
9. **Request Validation** - Size limits and timeouts
10. **Error Handling** - JSON-formatted error responses

**📖 [Read the complete API Gateway Guide](./GATEWAY_GUIDE.md)** for detailed explanations and learning exercises.

## 🔑 API Keys

Three valid API keys are configured:
- `dev-key-12345` - Development
- `test-key-67890` - Testing  
- `prod-key-abcdef` - Production

Include in requests as `X-API-Key` header.

## 🧪 Testing & Validation

### Comprehensive Test Suite
```bash
python3 validate_gateway.py
```
Tests all 10 gateway features with colored output and detailed results.

### Interactive Demo
```bash
chmod +x demo_gateway.sh
./demo_gateway.sh
```
Step-by-step demonstration of each feature with real API calls.

### Quick Tests
```bash
# All available commands
make help

# Specific feature tests
make test-auth          # Authentication
make test-cache         # Caching
make test-rate-limit    # Rate limiting
make test-discount      # Discount codes
make health             # Health checks
make metrics            # Gateway metrics
```

## 📡 API Endpoints

### Gateway Endpoints (No Auth Required)
- `GET /gateway/status` - Gateway version and status
- `GET /gateway/metrics` - NGINX stub_status metrics
- `GET /healthz` - Backend service health check

### Application Endpoints (Require API Key)
- `POST /v1/price` - Calculate price with VAT and discounts

**Example Request:**
```bash
curl -X POST http://localhost:8080/v1/price \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-key-12345" \
  -d '{
    "base_price": 100.0,
    "vat_rate": 0.2,
    "discount_code": "WELCOME10"
  }'
```

**Example Response:**
```json
{
  "base_price": 100.0,
  "vat_amount": 20.0,
  "discount_amount": 12.0,
  "final_price": 108.0,
  "applied_discount_code": "WELCOME10"
}
```

**Available Discount Codes:**
- `WELCOME10` - 10% off
- `VIP20` - 20% off
- `SAVE5` - 5% off

## 🏗️ Architecture

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │
       ▼
┌────────────────────────────────┐
│    NGINX API Gateway :8080     │
│  • Rate Limiting               │
│  • Authentication              │
│  • Caching                     │
│  • Load Balancing              │
└────────────┬───────────────────┘
             │
     ┌───────┴───────┬───────────┐
     ▼               ▼           ▼
┌─────────┐    ┌─────────┐  ┌─────────┐
│Backend 1│    │Backend 2│  │Backend 3│
│  :8000  │    │  :8001  │  │  :8002  │
└─────────┘    └─────────┘  └─────────┘
```

## 📊 Monitoring

### View Logs
```bash
make logs              # All services
make logs-nginx        # NGINX only
make logs-backend      # Backend services only
```

### Real-time Monitoring
```bash
# Follow access logs
docker-compose exec nginx tail -f /var/log/nginx/access.log

# Gateway metrics
make metrics
```

## 🛠️ Makefile Commands

Run `make help` to see all available commands:
```
  build           Build Docker images
  up              Start all services
  down            Stop all services
  logs            View logs from all services
  validate        Run comprehensive validation tests
  demo            Run interactive demo
  test-auth       Quick test of API key authentication
  test-cache      Test caching feature
  test-rate-limit Test rate limiting
  health          Check health of gateway and backends
  metrics         Show NGINX metrics
  clear-cache     Clear NGINX cache
  reload-nginx    Reload NGINX configuration
  clean           Stop services and remove volumes
```

## 🔧 Local Development (No Docker)

### 1. Create a virtual environment
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Run backend locally
```bash
# Using Make
make dev

# Or directly
export APP_ENV=local
uvicorn app.main:app --reload --port 8000
```

Open API docs at: http://localhost:8000/docs

### 4. Test without gateway
```bash
curl -X POST http://localhost:8000/v1/price \
  -H "Content-Type: application/json" \
  -d '{"base_price": 100.0, "discount_code": "WELCOME10"}'
```

## 🧪 Unit Tests
```bash
pytest -q
```

## ⚙️ Configuration

Environment variables (see `.env.example`):
- `APP_ENV` - Environment: `local`, `dev`, `prod`
- `LOG_LEVEL` - Logging level: `INFO`, `DEBUG`, `WARNING`
- `VAT_RATE_DEFAULT` - Default VAT rate (e.g., `0.2` for 20%)
- `SERVICE_INSTANCE` - Instance number for load balancing identification

## 📁 Project Structure
```
gateway-microservice/
├─ app/
│  ├─ api/
│  │  └─ routes.py              # API endpoints
│  ├─ core/
│  │  ├─ config.py              # Configuration
│  │  └─ logging.py             # Logging setup
│  ├─ models.py                 # Pydantic models
│  └─ main.py                   # FastAPI application
├─ tests/
│  └─ test_price.py             # Unit tests
├─ nginx.conf                    # NGINX gateway configuration
├─ docker-compose.yml            # Multi-container orchestration
├─ Dockerfile                    # Backend service image
├─ Makefile                      # Convenient commands
├─ validate_gateway.py           # Python validation suite
├─ demo_gateway.sh              # Interactive demo script
├─ GATEWAY_GUIDE.md             # Complete learning guide
├─ requirements.txt
└─ README.md
```

## 🎓 Learning Path

1. **Start Here**: Read [GATEWAY_GUIDE.md](./GATEWAY_GUIDE.md) for comprehensive explanations
2. **Hands-on**: Run `make validate` to see features in action
3. **Experiment**: Modify `nginx.conf` and test changes with `make reload-nginx`
4. **Exercises**: Try the learning exercises in the guide
5. **Advanced**: Explore logs with `make logs` to understand behavior

## 📝 Notes

- **Rate limits** are intentionally low for easy demonstration
- **Cache duration** is set to 5 minutes for testing
- **Load balancing** uses 3 instances for visibility
- **API keys** are hardcoded for simplicity (use external auth in production)
- **Pricing logic** is simple for demonstration purposes

## 🚧 Next Steps & Enhancements

- [ ] Implement JWT authentication
- [ ] Add Redis for distributed caching
- [ ] Implement circuit breaker pattern
- [ ] Add request/response transformation
- [ ] Export metrics to Prometheus
- [ ] Add distributed tracing (OpenTelemetry)
- [ ] Implement API versioning strategy
- [ ] Add request/response logging to database

## 🤝 Contributing

This is a learning project. Feel free to experiment and extend features!

## 📄 License

MIT License - feel free to use this project for learning and development.
