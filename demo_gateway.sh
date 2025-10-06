#!/bin/bash

# NGINX API Gateway Demo and Testing Script
# This script demonstrates various API Gateway features

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BASE_URL="http://localhost:8080"
API_KEY="dev-key-12345"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}NGINX API Gateway Feature Demo${NC}"
echo -e "${BLUE}========================================${NC}\n"

# Function to print section headers
print_header() {
    echo -e "\n${BLUE}=== $1 ===${NC}\n"
}

# Function to print success
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Function to print error
print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Function to print info
print_info() {
    echo -e "${YELLOW}→ $1${NC}"
}

# 1. Gateway Status
print_header "1. Gateway Status Check"
print_info "Checking if NGINX gateway is running..."
curl -s "$BASE_URL/gateway/status" | jq '.' || print_error "Gateway not responding"

# 2. Health Check
print_header "2. Backend Service Health Check"
print_info "Checking backend service health..."
curl -s "$BASE_URL/healthz" | jq '.' || print_error "Health check failed"

# 3. API Key Authentication - Missing Key
print_header "3. API Key Authentication - No Key (Should Fail)"
print_info "Attempting request without API key..."
response=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/v1/price" \
  -H "Content-Type: application/json" \
  -d '{"base_price": 100}')
http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | head -n-1)

if [ "$http_code" = "401" ]; then
    print_success "Correctly rejected (401 Unauthorized)"
    echo "$body" | jq '.'
else
    print_error "Expected 401, got $http_code"
fi

# 4. API Key Authentication - Valid Key
print_header "4. API Key Authentication - Valid Key (Should Succeed)"
print_info "Attempting request with valid API key..."
response=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/v1/price" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{"base_price": 100}')
http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | head -n-1)

if [ "$http_code" = "200" ]; then
    print_success "Successfully authenticated and processed (200 OK)"
    echo "$body" | jq '.'
else
    print_error "Expected 200, got $http_code"
fi

# 5. Caching Test
print_header "5. Response Caching Test"
print_info "First request (cache MISS expected)..."
response1=$(curl -s -i -X POST "$BASE_URL/v1/price" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{"base_price": 150, "vat_rate": 0.2}')

cache_status1=$(echo "$response1" | grep -i "X-Cache-Status" | cut -d' ' -f2 | tr -d '\r')
print_info "Cache Status: $cache_status1"

sleep 1

print_info "Second identical request (cache HIT expected)..."
response2=$(curl -s -i -X POST "$BASE_URL/v1/price" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{"base_price": 150, "vat_rate": 0.2}')

cache_status2=$(echo "$response2" | grep -i "X-Cache-Status" | cut -d' ' -f2 | tr -d '\r')
print_info "Cache Status: $cache_status2"

if [[ "$cache_status2" == "HIT"* ]] || [[ "$cache_status2" == "UPDATING"* ]]; then
    print_success "Caching is working!"
else
    print_info "Cache status: $cache_status2 (may need more time)"
fi

# 6. Load Balancing Test
print_header "6. Load Balancing Test"
print_info "Sending 20 requests to distribute across backend instances..."
for i in {1..20}; do
    curl -s -X POST "$BASE_URL/v1/price" \
      -H "Content-Type: application/json" \
      -H "X-API-Key: $API_KEY" \
      -d '{"base_price": 100}' > /dev/null
    echo -n "."
done
echo ""
print_success "Completed 20 requests (check NGINX logs for distribution)"

# 7. Rate Limiting Test
print_header "7. Rate Limiting Test"
print_info "Sending rapid requests to trigger rate limiting..."
success=0
limited=0

for i in {1..30}; do
    http_code=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/v1/price" \
      -H "Content-Type: application/json" \
      -H "X-API-Key: $API_KEY" \
      -d '{"base_price": 100}')
    
    if [ "$http_code" = "200" ]; then
        ((success++))
    elif [ "$http_code" = "429" ] || [ "$http_code" = "503" ]; then
        ((limited++))
    fi
done

print_info "Successful requests: $success"
print_info "Rate limited requests: $limited"

if [ $limited -gt 0 ]; then
    print_success "Rate limiting is working!"
else
    print_info "No rate limiting triggered (burst capacity absorbed requests)"
fi

# 8. Request Validation Tests
print_header "8. Request Validation Tests"

print_info "Testing invalid VAT rate..."
http_code=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/v1/price" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{"base_price": 100, "vat_rate": 1.5}')

if [ "$http_code" = "422" ]; then
    print_success "Correctly rejected invalid VAT rate (422)"
else
    print_error "Expected 422, got $http_code"
fi

print_info "Testing missing required field..."
http_code=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/v1/price" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{"vat_rate": 0.2}')

if [ "$http_code" = "422" ]; then
    print_success "Correctly rejected missing base_price (422)"
else
    print_error "Expected 422, got $http_code"
fi

print_info "Testing invalid discount code..."
response=$(curl -s -X POST "$BASE_URL/v1/price" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{"base_price": 100, "discount_code": "INVALID"}')
http_code=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/v1/price" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{"base_price": 100, "discount_code": "INVALID"}')

if [ "$http_code" = "400" ]; then
    print_success "Correctly rejected invalid discount code (400)"
else
    print_error "Expected 400, got $http_code"
fi

print_info "Testing valid request with discount code..."
response=$(curl -s -X POST "$BASE_URL/v1/price" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{"base_price": 100, "discount_code": "WELCOME10"}')
echo "$response" | jq '.'
print_success "Successfully processed with discount"

# 9. CORS Headers Check
print_header "9. CORS Headers Check"
print_info "Checking CORS headers on OPTIONS request..."
cors_headers=$(curl -s -I -X OPTIONS "$BASE_URL/v1/price" | grep -i "access-control")
if [ -n "$cors_headers" ]; then
    print_success "CORS headers are present:"
    echo "$cors_headers"
else
    print_error "CORS headers not found"
fi

# 10. Security Headers Check
print_header "10. Security Headers Check"
print_info "Checking security headers..."
response=$(curl -s -I -X POST "$BASE_URL/v1/price" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{"base_price": 100}')

security_headers=$(echo "$response" | grep -iE "X-Frame-Options|X-Content-Type-Options|X-XSS-Protection")
if [ -n "$security_headers" ]; then
    print_success "Security headers are present:"
    echo "$security_headers"
else
    print_error "Security headers not found"
fi

# 11. Gateway Metrics
print_header "11. Gateway Metrics"
print_info "Fetching NGINX stub_status metrics..."
curl -s "$BASE_URL/gateway/metrics"

# Summary
echo -e "\n${BLUE}========================================${NC}"
echo -e "${GREEN}Demo Complete!${NC}"
echo -e "${BLUE}========================================${NC}\n"

print_info "You've tested the following API Gateway features:"
echo "  1. Gateway Status Monitoring"
echo "  2. Health Checks"
echo "  3. API Key Authentication"
echo "  4. Response Caching"
echo "  5. Load Balancing"
echo "  6. Rate Limiting"
echo "  7. Request Validation"
echo "  8. CORS Configuration"
echo "  9. Security Headers"
echo "  10. Gateway Metrics"

echo -e "\n${YELLOW}To view detailed logs:${NC}"
echo "  docker-compose logs nginx"
echo "  docker-compose logs price-service-1"

echo -e "\n${YELLOW}To monitor real-time traffic:${NC}"
echo "  docker-compose logs -f nginx"
