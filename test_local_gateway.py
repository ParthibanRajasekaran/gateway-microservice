#!/usr/bin/env python3
"""
Test script for local gateway simulator
Tests basic API Gateway features without Docker
"""

import requests
import time
import json

BASE_URL = "http://localhost:8080"
VALID_API_KEY = "dev-key-12345"

print("="*60)
print("Testing Local API Gateway Simulator")
print("="*60)

# Test 1: Gateway Status
print("\n1. Testing gateway status...")
try:
    response = requests.get(f"{BASE_URL}/gateway/status")
    print(f"✓ Status: {response.status_code}")
    print(f"  {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"✗ Error: {e}")

# Test 2: Health Check (no auth required)
print("\n2. Testing health check (no auth)...")
try:
    response = requests.get(f"{BASE_URL}/healthz")
    print(f"✓ Status: {response.status_code}")
    print(f"  {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"✗ Error: {e}")

# Test 3: API without key (should fail)
print("\n3. Testing API without key (should fail with 401)...")
try:
    response = requests.post(
        f"{BASE_URL}/v1/price",
        json={"base_price": 100}
    )
    print(f"✓ Status: {response.status_code} (expected 401)")
    if response.status_code == 401:
        print(f"  {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"✗ Error: {e}")

# Test 4: API with valid key
print("\n4. Testing API with valid key...")
try:
    response = requests.post(
        f"{BASE_URL}/v1/price",
        json={"base_price": 100, "discount_code": "WELCOME10"},
        headers={"X-API-Key": VALID_API_KEY}
    )
    print(f"✓ Status: {response.status_code}")
    print(f"  Cache: {response.headers.get('X-Cache-Status', 'N/A')}")
    print(f"  Response Time: {response.headers.get('X-Response-Time', 'N/A')}s")
    print(f"  {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"✗ Error: {e}")

# Test 5: Caching (same request)
print("\n5. Testing caching (same request again)...")
time.sleep(0.5)
try:
    response = requests.post(
        f"{BASE_URL}/v1/price",
        json={"base_price": 100, "discount_code": "WELCOME10"},
        headers={"X-API-Key": VALID_API_KEY}
    )
    cache_status = response.headers.get('X-Cache-Status', 'N/A')
    print(f"✓ Status: {response.status_code}")
    print(f"  Cache: {cache_status} {'(✓ cached!)' if cache_status == 'HIT' else ''}")
    print(f"  Response Time: {response.headers.get('X-Response-Time', 'N/A')}s")
except Exception as e:
    print(f"✗ Error: {e}")

# Test 6: Rate Limiting
print("\n6. Testing rate limiting (sending 15 rapid requests)...")
try:
    success = 0
    rate_limited = 0
    
    for i in range(15):
        response = requests.post(
            f"{BASE_URL}/v1/price",
            json={"base_price": 100 + i},  # Different prices to avoid cache
            headers={"X-API-Key": VALID_API_KEY}
        )
        if response.status_code == 200:
            success += 1
        elif response.status_code == 429:
            rate_limited += 1
    
    print(f"  Successful: {success}")
    print(f"  Rate Limited: {rate_limited}")
    if rate_limited > 0:
        print(f"  ✓ Rate limiting is working!")
    else:
        print(f"  (Rate limit not triggered in this test)")
except Exception as e:
    print(f"✗ Error: {e}")

# Test 7: Gateway Stats
print("\n7. Checking gateway statistics...")
try:
    response = requests.get(f"{BASE_URL}/gateway/stats")
    print(f"✓ Status: {response.status_code}")
    print(f"  {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"✗ Error: {e}")

print("\n" + "="*60)
print("Tests Complete!")
print("="*60)
print("\nNote: This tests the local Python simulator.")
print("For full NGINX features, use Docker setup:")
print("  docker compose up --build -d")
print("  python3 validate_gateway.py")
print("="*60)
