#!/usr/bin/env python3
"""
Local API Gateway Simulator

This script simulates basic API Gateway features without Docker/NGINX.
It's useful for development and understanding gateway concepts.

Features simulated:
- API Key authentication
- Basic rate limiting
- Request logging
- Simple caching

Note: For full gateway experience, use Docker with NGINX.
"""

import asyncio
import time
from typing import Dict, Optional, Tuple
from collections import defaultdict, deque
from datetime import datetime
import httpx
import uvicorn
from fastapi import FastAPI, Request, Response, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
import json

# Configuration
BACKEND_URL = "http://localhost:8000"
GATEWAY_PORT = 8080

# Valid API keys
VALID_API_KEYS = {"dev-key-12345", "test-key-67890", "prod-key-abcdef"}

# Rate limiting: track requests per IP
request_tracker: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
RATE_LIMIT_REQUESTS = 10  # requests per window
RATE_LIMIT_WINDOW = 1  # second

# Simple cache
cache: Dict[str, Tuple[dict, float]] = {}
CACHE_TTL = 300  # 5 minutes

# Create gateway app
app = FastAPI(title="Local API Gateway", version="1.0.0")

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request counter for stats
request_stats = {
    "total_requests": 0,
    "auth_failures": 0,
    "rate_limited": 0,
    "cache_hits": 0,
    "cache_misses": 0,
}


def check_rate_limit(client_ip: str) -> bool:
    """Check if client has exceeded rate limit"""
    now = time.time()
    
    # Clean old requests
    while request_tracker[client_ip] and request_tracker[client_ip][0] < now - RATE_LIMIT_WINDOW:
        request_tracker[client_ip].popleft()
    
    # Check limit
    if len(request_tracker[client_ip]) >= RATE_LIMIT_REQUESTS:
        return False
    
    # Add current request
    request_tracker[client_ip].append(now)
    return True


def get_cache_key(method: str, path: str, body: bytes, api_key: str) -> str:
    """Generate cache key"""
    return f"{method}:{path}:{api_key}:{body.decode()}"


def get_from_cache(cache_key: str) -> Optional[dict]:
    """Get response from cache if valid"""
    if cache_key in cache:
        data, timestamp = cache[cache_key]
        if time.time() - timestamp < CACHE_TTL:
            return data
        else:
            del cache[cache_key]
    return None


def set_cache(cache_key: str, data: dict):
    """Store response in cache"""
    cache[cache_key] = (data, time.time())


@app.get("/gateway/status")
async def gateway_status():
    """Gateway status endpoint"""
    return {
        "gateway": "local-python-simulator",
        "status": "running",
        "version": "1.0.0",
        "backend": BACKEND_URL,
        "note": "This is a simulated gateway. Use Docker for full NGINX features."
    }


@app.get("/gateway/stats")
async def gateway_stats():
    """Gateway statistics"""
    return {
        "stats": request_stats,
        "cache_size": len(cache),
        "rate_limit_config": {
            "requests_per_window": RATE_LIMIT_REQUESTS,
            "window_seconds": RATE_LIMIT_WINDOW
        }
    }


@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
async def gateway_proxy(
    request: Request,
    path: str,
    x_api_key: Optional[str] = Header(None)
):
    """Main gateway proxy with authentication, rate limiting, and caching"""
    
    request_stats["total_requests"] += 1
    client_ip = request.client.host
    start_time = time.time()
    
    # Skip auth for health check
    if path != "healthz":
        # 1. API Key Authentication
        if not x_api_key or x_api_key not in VALID_API_KEYS:
            request_stats["auth_failures"] += 1
            raise HTTPException(
                status_code=401,
                detail={
                    "error": "Invalid or missing API key",
                    "message": "Please provide a valid X-API-Key header",
                    "valid_keys_hint": "dev-key-12345, test-key-67890, prod-key-abcdef"
                }
            )
        
        # 2. Rate Limiting
        if not check_rate_limit(client_ip):
            request_stats["rate_limited"] += 1
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "Rate limit exceeded",
                    "message": f"Maximum {RATE_LIMIT_REQUESTS} requests per {RATE_LIMIT_WINDOW} second(s)",
                    "retry_after": 1
                }
            )
    
    # Prepare request to backend
    method = request.method
    url = f"{BACKEND_URL}/{path}"
    headers = dict(request.headers)
    headers.pop("host", None)  # Remove host header
    
    # Get request body
    body = await request.body()
    
    # 3. Check cache (only for POST to /v1/price)
    cache_status = "BYPASS"
    cached_response = None
    
    if method == "POST" and path == "v1/price" and x_api_key:
        cache_key = get_cache_key(method, path, body, x_api_key)
        cached_response = get_from_cache(cache_key)
        
        if cached_response:
            cache_status = "HIT"
            request_stats["cache_hits"] += 1
            response_time = time.time() - start_time
            
            # Return cached response
            return Response(
                content=json.dumps(cached_response),
                media_type="application/json",
                headers={
                    "X-Cache-Status": cache_status,
                    "X-Response-Time": str(response_time),
                    "X-Gateway": "local-simulator"
                }
            )
        else:
            cache_status = "MISS"
            request_stats["cache_misses"] += 1
    
    # 4. Forward request to backend
    try:
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=method,
                url=url,
                headers=headers,
                content=body,
                timeout=10.0
            )
        
        response_time = time.time() - start_time
        
        # 5. Cache successful responses
        if method == "POST" and path == "v1/price" and response.status_code == 200 and x_api_key:
            cache_key = get_cache_key(method, path, body, x_api_key)
            try:
                response_data = response.json()
                set_cache(cache_key, response_data)
            except:
                pass
        
        # Log request
        print(f"[{datetime.now().isoformat()}] {client_ip} {method} /{path} "
              f"{response.status_code} {response_time:.4f}s cache={cache_status}")
        
        # 6. Return response with gateway headers
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers={
                **dict(response.headers),
                "X-Cache-Status": cache_status,
                "X-Response-Time": str(response_time),
                "X-Gateway": "local-simulator",
                "Access-Control-Allow-Origin": "*",
            }
        )
    
    except httpx.ConnectError:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "Backend service unavailable",
                "message": f"Could not connect to backend at {BACKEND_URL}",
                "hint": "Make sure the backend service is running on port 8000"
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Gateway error",
                "message": str(e)
            }
        )


def print_banner():
    """Print startup banner"""
    print("\n" + "="*60)
    print("🚀 Local API Gateway Simulator")
    print("="*60)
    print(f"Gateway URL: http://localhost:{GATEWAY_PORT}")
    print(f"Backend URL: {BACKEND_URL}")
    print(f"\nFeatures:")
    print(f"  ✓ API Key Authentication")
    print(f"  ✓ Rate Limiting ({RATE_LIMIT_REQUESTS} req/{RATE_LIMIT_WINDOW}s per IP)")
    print(f"  ✓ Response Caching (TTL: {CACHE_TTL}s)")
    print(f"  ✓ Request Logging")
    print(f"  ✓ CORS Support")
    print(f"\nValid API Keys:")
    print(f"  • dev-key-12345")
    print(f"  • test-key-67890")
    print(f"  • prod-key-abcdef")
    print(f"\nEndpoints:")
    print(f"  • GET  /gateway/status - Gateway status")
    print(f"  • GET  /gateway/stats  - Gateway statistics")
    print(f"  • GET  /healthz        - Backend health (no auth)")
    print(f"  • POST /v1/price       - Price API (requires auth)")
    print(f"\nNote: This is a simplified simulator.")
    print(f"      For full NGINX features, use Docker setup.")
    print("="*60 + "\n")


if __name__ == "__main__":
    print_banner()
    
    print("Starting gateway on port", GATEWAY_PORT)
    print("Make sure backend is running on port 8000!\n")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=GATEWAY_PORT,
        log_level="warning"  # Reduce noise, we have custom logging
    )
