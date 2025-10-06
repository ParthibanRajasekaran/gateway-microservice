# Quick Start Guide - No Docker Required

This guide helps you test API Gateway concepts without Docker.

## 🚀 Quick Start (3 Steps)

### Step 1: Start the Backend Service

Open a terminal and run:

```bash
# Activate your virtual environment if using one
source .venv/bin/activate

# Start the backend on port 8000
uvicorn app.main:app --reload --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### Step 2: Start the Local Gateway Simulator

Open a **second terminal** and run:

```bash
# Activate your virtual environment
source .venv/bin/activate

# Start the gateway simulator on port 8080
python3 local_gateway.py
```

You should see:
```
🚀 Local API Gateway Simulator
Gateway URL: http://localhost:8080
Backend URL: http://localhost:8000

Features:
  ✓ API Key Authentication
  ✓ Rate Limiting (10 req/1s per IP)
  ✓ Response Caching (TTL: 300s)
  ✓ Request Logging
  ✓ CORS Support

Valid API Keys:
  • dev-key-12345
  • test-key-67890
  • prod-key-abcdef
```

### Step 3: Test the Gateway

Open a **third terminal** and run:

```bash
python3 test_local_gateway.py
```

Or test manually:

```bash
# Test without API key (should fail with 401)
curl -X POST http://localhost:8080/v1/price \
  -H "Content-Type: application/json" \
  -d '{"base_price": 100}'

# Test with valid API key (should succeed)
curl -X POST http://localhost:8080/v1/price \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-key-12345" \
  -d '{"base_price": 100, "discount_code": "WELCOME10"}'
```

## 🎯 What You Can Learn

### 1. API Key Authentication
- Requests without API keys are rejected (401)
- Only valid API keys can access protected endpoints
- Health check doesn't require authentication

**Try it:**
```bash
# No key - FAILS
curl http://localhost:8080/v1/price \
  -H "Content-Type: application/json" \
  -d '{"base_price": 100}'

# Valid key - SUCCEEDS
curl http://localhost:8080/v1/price \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-key-12345" \
  -d '{"base_price": 100}'
```

### 2. Rate Limiting
- Limited to 10 requests per second per IP address
- Excess requests get 429 (Too Many Requests)

**Try it:**
```bash
# Send rapid requests
for i in {1..15}; do
  curl -s -o /dev/null -w "%{http_code} " \
    -X POST http://localhost:8080/v1/price \
    -H "Content-Type: application/json" \
    -H "X-API-Key: dev-key-12345" \
    -d "{\"base_price\": $((100 + i))}"
done
echo ""
```

You should see some `429` responses (rate limited).

### 3. Response Caching
- Identical POST requests are cached for 5 minutes
- Cache key includes API key, so different users get separate caches
- Check `X-Cache-Status` header: MISS (first time) or HIT (cached)

**Try it:**
```bash
# First request - cache MISS
curl -i -X POST http://localhost:8080/v1/price \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-key-12345" \
  -d '{"base_price": 150}' | grep X-Cache-Status

# Second request - cache HIT
curl -i -X POST http://localhost:8080/v1/price \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-key-12345" \
  -d '{"base_price": 150}' | grep X-Cache-Status
```

### 4. Request Logging
- Watch the gateway terminal to see request logs
- Shows: timestamp, IP, method, path, status, response time, cache status

Example log:
```
[2025-10-06T...] 127.0.0.1 POST /v1/price 200 0.0234s cache=MISS
[2025-10-06T...] 127.0.0.1 POST /v1/price 200 0.0012s cache=HIT
```

### 5. Gateway Statistics
```bash
curl http://localhost:8080/gateway/stats | jq
```

Shows:
- Total requests
- Authentication failures
- Rate limited requests
- Cache hits/misses
- Cache size

## 🔍 Features Comparison

### Local Simulator (No Docker) ✅
- ✅ API Key Authentication
- ✅ Basic Rate Limiting
- ✅ Response Caching
- ✅ Request Logging
- ✅ CORS Support
- ⚠️  Single backend instance
- ⚠️  In-memory cache (not persistent)
- ⚠️  Basic rate limiting (not production-grade)

### Full NGINX Setup (With Docker) 🚀
- ✅ API Key Authentication
- ✅ Production-grade Rate Limiting
- ✅ Advanced Caching with disk persistence
- ✅ Load Balancing (3 backend instances)
- ✅ Health Checks & Auto-failover
- ✅ Request/Response buffering
- ✅ Compression
- ✅ Security headers
- ✅ Metrics endpoint
- ✅ Persistent logging

## 📚 Next Steps

### To Learn More:
1. **Read the code**: Open `local_gateway.py` to see how features are implemented
2. **Experiment**: Modify rate limits, cache TTL, or API keys
3. **Check logs**: Watch both terminals to see request flow

### To Get Full Experience:
1. **Install Docker Desktop**: https://www.docker.com/products/docker-desktop
2. **Run the full setup**:
   ```bash
   docker compose up --build -d
   python3 validate_gateway.py
   ```
3. **Read the complete guide**: [GATEWAY_GUIDE.md](./GATEWAY_GUIDE.md)

## 🐛 Troubleshooting

**Problem**: "Connection refused" when testing
- **Solution**: Make sure both backend (port 8000) and gateway (port 8080) are running

**Problem**: Port already in use
- **Solution**: 
  ```bash
  # Kill process on port 8000 or 8080
  lsof -ti :8000 | xargs kill -9
  lsof -ti :8080 | xargs kill -9
  ```

**Problem**: ModuleNotFoundError: No module named 'httpx'
- **Solution**: 
  ```bash
  pip install httpx
  ```

## 💡 Understanding the Differences

### Local Simulator
- **Purpose**: Learning and development
- **Technology**: Python/FastAPI
- **Pros**: Easy to setup, no Docker needed, readable code
- **Cons**: Limited features, not production-ready

### NGINX Gateway
- **Purpose**: Production use
- **Technology**: NGINX (C-based, highly optimized)
- **Pros**: High performance, battle-tested, feature-rich
- **Cons**: Requires Docker, more complex configuration

## 🎓 Learning Exercises

### Exercise 1: Modify Rate Limit
1. Open `local_gateway.py`
2. Change `RATE_LIMIT_REQUESTS` from 10 to 5
3. Restart the gateway
4. Test with rapid requests

### Exercise 2: Add New API Key
1. Open `local_gateway.py`
2. Add a new key to `VALID_API_KEYS` set
3. Restart the gateway
4. Test with your new key

### Exercise 3: Observe Cache Behavior
1. Send a request and note the response time
2. Send the same request again
3. Compare response times (cached should be faster)
4. Wait 5+ minutes and try again (cache expired)

### Exercise 4: Monitor Statistics
1. Reset stats by restarting gateway
2. Run various tests
3. Check stats: `curl http://localhost:8080/gateway/stats`
4. Analyze the numbers

## 📖 Related Files

- `local_gateway.py` - Gateway simulator (read this to understand implementation)
- `test_local_gateway.py` - Automated test suite
- `app/main.py` - Backend service
- `app/api/routes.py` - API endpoints
- `GATEWAY_GUIDE.md` - Complete guide for full NGINX setup
- `SETUP.md` - Installation instructions

## ✨ Summary

You now have a working API Gateway simulator that demonstrates:
- How authentication protects APIs
- How rate limiting prevents abuse
- How caching improves performance
- How logging helps monitoring

When you're ready for production-grade features, move to the Docker/NGINX setup!
