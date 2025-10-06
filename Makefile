.PHONY: help build up down logs test demo clean validate

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-15s %s\n", $$1, $$2}'

build: ## Build Docker images
	docker-compose build

up: ## Start all services (NGINX + 3 backend instances)
	docker-compose up -d
	@echo "Waiting for services to be ready..."
	@sleep 5
	@echo "✓ Gateway running at http://localhost:8080"
	@echo "✓ Backend services running on ports 8000, 8001, 8002"

down: ## Stop all services
	docker-compose down

restart: ## Restart all services
	docker-compose restart

logs: ## View logs from all services
	docker-compose logs -f

logs-nginx: ## View NGINX logs only
	docker-compose logs -f nginx

logs-backend: ## View backend service logs
	docker-compose logs -f price-service-1 price-service-2 price-service-3

status: ## Check status of all services
	docker-compose ps

validate: up ## Run comprehensive validation tests
	@echo "Running validation tests..."
	@sleep 3
	python3 validate_gateway.py

demo: up ## Run interactive demo
	@echo "Running feature demo..."
	@sleep 3
	@chmod +x demo_gateway.sh
	./demo_gateway.sh

test-auth: ## Quick test of API key authentication
	@echo "Testing without API key (should fail):"
	@curl -s -X POST http://localhost:8080/v1/price \
		-H "Content-Type: application/json" \
		-d '{"base_price": 100}' | jq
	@echo "\nTesting with valid API key (should succeed):"
	@curl -s -X POST http://localhost:8080/v1/price \
		-H "Content-Type: application/json" \
		-H "X-API-Key: dev-key-12345" \
		-d '{"base_price": 100}' | jq

test-cache: ## Test caching feature
	@echo "First request (cache MISS):"
	@curl -s -i -X POST http://localhost:8080/v1/price \
		-H "Content-Type: application/json" \
		-H "X-API-Key: dev-key-12345" \
		-d '{"base_price": 150, "vat_rate": 0.2}' 2>&1 | grep -i "x-cache-status"
	@sleep 1
	@echo "Second request (cache HIT):"
	@curl -s -i -X POST http://localhost:8080/v1/price \
		-H "Content-Type: application/json" \
		-H "X-API-Key: dev-key-12345" \
		-d '{"base_price": 150, "vat_rate": 0.2}' 2>&1 | grep -i "x-cache-status"

test-rate-limit: ## Test rate limiting
	@echo "Sending 30 rapid requests..."
	@for i in $$(seq 1 30); do \
		curl -s -o /dev/null -w "%{http_code} " \
			-X POST http://localhost:8080/v1/price \
			-H "Content-Type: application/json" \
			-H "X-API-Key: dev-key-12345" \
			-d '{"base_price": 100}'; \
	done
	@echo "\n(429 or 503 = rate limited, 200 = success)"

test-discount: ## Test with discount code
	@echo "Testing WELCOME10 discount (10% off):"
	@curl -s -X POST http://localhost:8080/v1/price \
		-H "Content-Type: application/json" \
		-H "X-API-Key: dev-key-12345" \
		-d '{"base_price": 100, "vat_rate": 0.2, "discount_code": "WELCOME10"}' | jq

health: ## Check health of gateway and backends
	@echo "Gateway status:"
	@curl -s http://localhost:8080/gateway/status | jq
	@echo "\nBackend health:"
	@curl -s http://localhost:8080/healthz | jq

metrics: ## Show NGINX metrics
	@curl -s http://localhost:8080/gateway/metrics

clear-cache: ## Clear NGINX cache
	docker-compose exec nginx rm -rf /var/cache/nginx/*
	@echo "Cache cleared!"

reload-nginx: ## Reload NGINX configuration
	docker-compose exec nginx nginx -s reload
	@echo "NGINX configuration reloaded!"

test-nginx-config: ## Test NGINX configuration syntax
	docker-compose exec nginx nginx -t

shell-nginx: ## Open shell in NGINX container
	docker-compose exec nginx sh

shell-backend: ## Open shell in backend container
	docker-compose exec price-service-1 sh

clean: down ## Stop services and remove volumes
	docker-compose down -v
	@echo "Cleaned up all containers and volumes"

clean-all: ## Remove everything including images
	docker-compose down -v --rmi all
	@echo "Cleaned up containers, volumes, and images"

install-deps: ## Install Python dependencies locally
	pip install -r requirements.txt

dev: ## Run backend service locally (without Docker)
	uvicorn app.main:app --reload --port 8000

.DEFAULT_GOAL := help
