# NGINX API Gateway Learning Guide

## Overview
This project demonstrates a production-grade API Gateway using NGINX with a FastAPI backend service. The gateway implements essential API Gateway patterns and features.

## Architecture

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │
       ▼
┌──────────────────────────────────────┐
│         NGINX API Gateway            │
│  ┌────────────────────────────────┐  │
│  │ Rate Limiting                  │  │
│  │ Authentication (API Keys)      │  │
│  │ Caching                        │  │
│  │ Load Balancing                 │  │
│  │ Request/Response Logging       │  │
│  │ CORS & Security Headers        │  │
│  └────────────────────────────────┘  │
└──────────────┬───────────────────────┘
               │
       ┌───────┴───────┬───────────┐
       ▼               ▼           ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│ Backend #1  │ │ Backend #2  │ │ Backend #3  │
│ (Primary)   │ │ (Backup)    │ │ (Backup)    │
└─────────────┘ └─────────────┘ └─────────────┘
```

## Features Implemented

### 1. **Rate Limiting**
- **IP-based limiting**: 10 requests/second per IP address
- **API key-based limiting**: 100 requests/second per API key
- **Burst capacity**: Allows temporary bursts above the rate limit
- **Connection limiting**: Maximum 10 concurrent connections per IP

**Configuration**: 
```nginx
limit_req_zone $binary_remote_addr zone=ip_limit:10m rate=10r/s;
limit_req_zone $http_x_api_key zone=api_key_limit:10m rate=100r/s;
```

**Why it matters**: Prevents abuse and ensures fair resource distribution.

### 2. **Load Balancing**
- **Strategy**: Least connections (sends requests to server with fewest active connections)
- **Health checking**: Marks servers as down after 3 failed attempts
- **Backup servers**: Automatically failover to backup servers if primary fails
- **Keep-alive connections**: Maintains persistent connections for better performance

**Configuration**:
```nginx
upstream price_service_backend {
    least_conn;
    server host.docker.internal:8000 max_fails=3 fail_timeout=30s;
    server host.docker.internal:8001 backup;
    server host.docker.internal:8002 backup;
}
```

**Why it matters**: Distributes traffic, provides high availability, and improves performance.

### 3. **Response Caching**
- **Cache duration**: 5 minutes for successful responses (200)
- **Cache key**: Includes API key for per-user caching
- **Stale-while-revalidate**: Serves stale cache during updates
- **Background updates**: Updates cache without blocking requests
- **Cache headers**: `X-Cache-Status` shows HIT/MISS/UPDATING

**Configuration**:
```nginx
proxy_cache_path /var/cache/nginx/api_cache levels=1:2 keys_zone=api_cache:10m;
proxy_cache_valid 200 5m;
proxy_cache_use_stale error timeout updating;
```

**Why it matters**: Reduces backend load and improves response times significantly.

### 4. **Authentication (API Key)**
- **Header-based**: Uses `X-API-Key` header
- **Map-based validation**: Efficient lookup using NGINX maps
- **Pre-configured keys**: Three valid API keys for different environments

**Valid API Keys**:
- `dev-key-12345` - Development
- `test-key-67890` - Testing
- `prod-key-abcdef` - Production

**Configuration**:
```nginx
map $http_x_api_key $is_valid_api_key {
    default 0;
    "dev-key-12345" 1;
    "test-key-67890" 1;
    "prod-key-abcdef" 1;
}
```

**Why it matters**: Secures API access and enables per-client tracking.

### 5. **CORS Configuration**
- **Origins**: Allows all origins (configurable)
- **Methods**: GET, POST, OPTIONS
- **Headers**: Content-Type, X-API-Key
- **Preflight handling**: Automatic OPTIONS response

**Why it matters**: Enables browser-based clients to access the API.

### 6. **Security Headers**
- `X-Frame-Options`: Prevents clickjacking
- `X-Content-Type-Options`: Prevents MIME type sniffing
- `X-XSS-Protection`: Enables XSS filter

**Why it matters**: Protects against common web vulnerabilities.

### 7. **Request/Response Logging**
- **Custom log format**: Includes response times, cache status, API keys
- **Structured logging**: Easy to parse for monitoring tools
- **Separate access and error logs**

**Log Format**:
```nginx
log_format api_gateway '$remote_addr - $remote_user [$time_local] '
                      '"$request" $status $body_bytes_sent '
                      'rt=$request_time api_key=$http_x_api_key';
```

### 8. **Health Checks**
- **Gateway status**: `/gateway/status` - Returns gateway info
- **Backend health**: `/healthz` - Proxied to backend services
- **Metrics**: `/gateway/metrics` - NGINX stub_status metrics

### 9. **Request Size Limits**
- **Maximum body size**: 1MB
- **Timeouts**: 5s connect, 10s send/read

**Why it matters**: Prevents resource exhaustion from large requests.

### 10. **Error Handling**
- **Custom error responses**: JSON-formatted errors
- **404 for undefined routes**: Clear error messages
- **401 for authentication failures**: Explains missing/invalid API key

## Quick Start

### 1. Start the Gateway and Backend Services
```bash
# Build and start all services
docker-compose up --build -d

# Check status
docker-compose ps
```

### 2. Run Validation Tests

#### Option A: Python Script (Detailed)
```bash
python3 validate_gateway.py
```

#### Option B: Bash Script (Quick Demo)
```bash
chmod +x demo_gateway.sh
./demo_gateway.sh
```

### 3. Test Individual Features

#### Test Authentication
```bash
# Without API key (should fail with 401)
curl -X POST http://localhost:8080/v1/price \
  -H "Content-Type: application/json" \
  -d '{"base_price": 100}'

# With valid API key (should succeed)
curl -X POST http://localhost:8080/v1/price \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-key-12345" \
  -d '{"base_price": 100}'
```

#### Test Caching
```bash
# First request (cache MISS)
curl -i -X POST http://localhost:8080/v1/price \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-key-12345" \
  -d '{"base_price": 150, "vat_rate": 0.2}' | grep X-Cache-Status

# Second request (cache HIT)
curl -i -X POST http://localhost:8080/v1/price \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-key-12345" \
  -d '{"base_price": 150, "vat_rate": 0.2}' | grep X-Cache-Status
```

#### Test Rate Limiting
```bash
# Send rapid requests
for i in {1..30}; do
  curl -s -o /dev/null -w "%{http_code}\n" \
    -X POST http://localhost:8080/v1/price \
    -H "Content-Type: application/json" \
    -H "X-API-Key: dev-key-12345" \
    -d '{"base_price": 100}'
done
```

#### Test with Discount Code
```bash
curl -X POST http://localhost:8080/v1/price \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-key-12345" \
  -d '{"base_price": 100, "discount_code": "WELCOME10"}' | jq
```

## Monitoring

### View Logs
```bash
# All logs
docker-compose logs -f

# NGINX logs only
docker-compose logs -f nginx

# Specific service logs
docker-compose logs -f price-service-1
```

### Check Gateway Metrics
```bash
curl http://localhost:8080/gateway/metrics
```

### Monitor Real-time Traffic
```bash
# Follow NGINX access logs
docker-compose exec nginx tail -f /var/log/nginx/access.log

# Follow error logs
docker-compose exec nginx tail -f /var/log/nginx/error.log
```

## API Endpoints

### Gateway Endpoints
- `GET /gateway/status` - Gateway status and version
- `GET /gateway/metrics` - NGINX metrics (stub_status)
- `GET /healthz` - Backend service health check

### Application Endpoints (require API key)
- `POST /v1/price` - Calculate price with VAT and discounts

**Request Body**:
```json
{
  "base_price": 100.0,
  "vat_rate": 0.2,
  "discount_code": "WELCOME10"
}
```

**Response**:
```json
{
  "base_price": 100.0,
  "vat_amount": 20.0,
  "discount_amount": 12.0,
  "final_price": 108.0,
  "applied_discount_code": "WELCOME10"
}
```

**Available Discount Codes**:
- `WELCOME10` - 10% off
- `VIP20` - 20% off
- `SAVE5` - 5% off

## Learning Exercises

### Exercise 1: Observe Load Balancing
1. Send multiple requests and check which backend handles them
2. View logs: `docker-compose logs price-service-1 price-service-2 price-service-3`
3. Stop one backend: `docker-compose stop price-service-1`
4. Send more requests and observe failover

### Exercise 2: Measure Cache Performance
1. Clear cache: `docker-compose exec nginx rm -rf /var/cache/nginx/*`
2. Send request and measure time: `time curl ...`
3. Send same request again and compare time
4. Check `X-Cache-Status` header

### Exercise 3: Test Rate Limiting
1. Use the rate limit test script
2. Monitor rejected requests
3. Modify rate in `nginx.conf` and reload: `docker-compose exec nginx nginx -s reload`

### Exercise 4: Add New API Key
1. Edit `nginx.conf`, add new key to map
2. Reload NGINX: `docker-compose exec nginx nginx -s reload`
3. Test with new key

### Exercise 5: Modify Cache Duration
1. Edit cache duration in `nginx.conf`
2. Reload NGINX
3. Test and verify new cache behavior

## Troubleshooting

### Gateway not starting
```bash
# Check NGINX configuration syntax
docker-compose exec nginx nginx -t

# View error logs
docker-compose logs nginx
```

### Backend services not responding
```bash
# Check service status
docker-compose ps

# Check individual service logs
docker-compose logs price-service-1

# Restart services
docker-compose restart
```

### Cache not working
```bash
# Clear cache
docker-compose exec nginx rm -rf /var/cache/nginx/*

# Verify cache directory permissions
docker-compose exec nginx ls -la /var/cache/nginx/
```

## Advanced Topics

### 1. Custom Load Balancing Strategies
- `round_robin` (default)
- `least_conn` (current)
- `ip_hash` (sticky sessions)
- `random`

### 2. Advanced Caching
- Cache locking
- Cache revalidation
- Vary header support
- Cache purging

### 3. Additional Rate Limiting
- Distributed rate limiting with Redis
- Dynamic rate limits based on API tier
- Graceful degradation

### 4. Enhanced Security
- JWT validation
- mTLS (mutual TLS)
- Request signature validation
- WAF (Web Application Firewall) rules

## Clean Up

```bash
# Stop all services
docker-compose down

# Remove volumes (including cache)
docker-compose down -v

# Remove images
docker-compose down --rmi all
```

## Next Steps

1. **Implement JWT Authentication**: Replace simple API keys with JWT tokens
2. **Add Redis for Distributed Caching**: Share cache across multiple NGINX instances
3. **Implement Circuit Breaker**: Fail fast when backend is down
4. **Add Request Transformation**: Modify requests/responses in transit
5. **Implement API Versioning**: Route to different backends based on version
6. **Add Metrics Export**: Export metrics to Prometheus/Grafana
7. **Implement Blue-Green Deployment**: Zero-downtime deployments

## Resources

- [NGINX Documentation](https://nginx.org/en/docs/)
- [API Gateway Patterns](https://microservices.io/patterns/apigateway.html)
- [Rate Limiting Best Practices](https://cloud.google.com/architecture/rate-limiting-strategies)
- [Caching Strategies](https://www.nginx.com/blog/nginx-caching-guide/)
