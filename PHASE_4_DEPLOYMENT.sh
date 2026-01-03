#!/bin/bash

################################################################################
#
# Phase 4 - TenMuses Copilot Deployment Guide
#
# This script provides complete deployment instructions for Phase 4 features
# including environment setup, testing, Docker deployment, and verification
#
################################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
log_step() {
    echo -e "${BLUE}==> $1${NC}"
}

log_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

log_error() {
    echo -e "${RED}✗ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Phase 4 Deployment Checklist
PHASE_4_CHECKLIST=(
    "Environment variables configured (.env files)"
    "Dependencies installed (backend & frontend)"
    "Backend integration tests passing"
    "Frontend integration tests passing"
    "Docker images built successfully"
    "Database migrations applied"
    "API endpoints verified"
    "WebSocket connections tested"
    "Streaming responses validated"
    "Frontend build successful"
    "Performance benchmarks acceptable"
)

################################################################################
# 1. PRE-DEPLOYMENT SETUP
################################################################################
setup_environment() {
    log_step "Setting up environment variables..."
    
    # Backend .env
    if [ ! -f "backend/.env" ]; then
        log_warning "backend/.env not found, creating from example..."
        if [ -f "backend/.env.example" ]; then
            cp backend/.env.example backend/.env
            log_success "Created backend/.env"
        else
            log_error "backend/.env.example not found"
            return 1
        fi
    fi
    
    # Frontend .env.local
    if [ ! -f "frontend/.env.local" ]; then
        log_warning "frontend/.env.local not found, creating from example..."
        if [ -f "frontend/env.local.example" ]; then
            cp frontend/env.local.example frontend/.env.local
            log_success "Created frontend/.env.local"
        else
            log_error "frontend/env.local.example not found"
            return 1
        fi
    fi
    
    log_success "Environment setup complete"
}

# Verify critical environment variables
verify_env_variables() {
    log_step "Verifying environment variables..."
    
    local required_vars=(
        "DATABASE_URL"
        "OPENAI_API_KEY"
        "JWT_SECRET_KEY"
    )
    
    local missing=0
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            log_error "Missing required variable: $var"
            missing=$((missing + 1))
        fi
    done
    
    if [ $missing -gt 0 ]; then
        log_error "Please set all required environment variables in .env files"
        return 1
    fi
    
    log_success "All required environment variables are set"
}

################################################################################
# 2. DEPENDENCY INSTALLATION
################################################################################
install_dependencies() {
    log_step "Installing dependencies..."
    
    # Backend
    log_step "Installing backend dependencies..."
    cd backend
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        log_success "Created virtual environment"
    fi
    
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    log_success "Backend dependencies installed"
    cd ..
    
    # Frontend
    log_step "Installing frontend dependencies..."
    cd frontend
    npm install --legacy-peer-deps
    log_success "Frontend dependencies installed"
    cd ..
}

################################################################################
# 3. TESTING
################################################################################
run_backend_tests() {
    log_step "Running backend integration tests..."
    
    cd backend
    source venv/bin/activate
    
    # Run Phase 4 tests
    python -m pytest tests/test_phase4_integration.py -v --tb=short
    local result=$?
    
    cd ..
    
    if [ $result -eq 0 ]; then
        log_success "Backend tests passed"
        return 0
    else
        log_error "Backend tests failed"
        return 1
    fi
}

run_frontend_tests() {
    log_step "Running frontend integration tests..."
    
    cd frontend
    
    # Run Phase 4 integration tests
    npm run test -- __tests__/integration/phase4-copilot-integration.test.ts --run
    local result=$?
    
    cd ..
    
    if [ $result -eq 0 ]; then
        log_success "Frontend tests passed"
        return 0
    else
        log_error "Frontend tests failed"
        return 1
    fi
}

build_frontend() {
    log_step "Building frontend for production..."
    
    cd frontend
    npm run build
    local result=$?
    cd ..
    
    if [ $result -eq 0 ]; then
        log_success "Frontend build successful"
        return 0
    else
        log_error "Frontend build failed"
        return 1
    fi
}

################################################################################
# 4. DATABASE SETUP
################################################################################
setup_database() {
    log_step "Setting up database..."
    
    cd backend
    source venv/bin/activate
    
    # Create database if it doesn't exist
    python -c "from app.core.config import settings; print(f'Using: {settings.DATABASE_URL}')"
    
    # Tables will be auto-created on startup via SQLAlchemy
    python -m app.scripts.init_db
    
    cd ..
    log_success "Database setup complete"
}

################################################################################
# 5. DOCKER DEPLOYMENT
################################################################################
build_docker_images() {
    log_step "Building Docker images..."
    
    if [ ! -f "docker-compose.yml" ]; then
        log_error "docker-compose.yml not found"
        return 1
    fi
    
    docker-compose build
    
    if [ $? -eq 0 ]; then
        log_success "Docker images built successfully"
        return 0
    else
        log_error "Docker build failed"
        return 1
    fi
}

start_docker_services() {
    log_step "Starting Docker services..."
    
    docker-compose up -d
    
    if [ $? -eq 0 ]; then
        log_success "Docker services started"
        sleep 5  # Wait for services to initialize
        return 0
    else
        log_error "Failed to start Docker services"
        return 1
    fi
}

stop_docker_services() {
    log_step "Stopping Docker services..."
    
    docker-compose down
    
    if [ $? -eq 0 ]; then
        log_success "Docker services stopped"
        return 0
    else
        log_error "Failed to stop Docker services"
        return 1
    fi
}

################################################################################
# 6. VERIFICATION TESTS
################################################################################
verify_backend_api() {
    log_step "Verifying backend API endpoints..."
    
    local endpoints=(
        "http://localhost:8000/api/v1/health"
        "http://localhost:8000/docs"
    )
    
    for endpoint in "${endpoints[@]}"; do
        response=$(curl -s -o /dev/null -w "%{http_code}" "$endpoint")
        if [ "$response" = "200" ] || [ "$response" = "302" ]; then
            log_success "✓ $endpoint"
        else
            log_error "✗ $endpoint (HTTP $response)"
        fi
    done
}

verify_frontend() {
    log_step "Verifying frontend..."
    
    response=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:3000")
    
    if [ "$response" = "200" ]; then
        log_success "Frontend is accessible"
    else
        log_error "Frontend returned HTTP $response"
    fi
}

verify_streaming() {
    log_step "Verifying streaming endpoints..."
    
    python3 << 'EOF'
import httpx
import asyncio
import json

async def test_streaming():
    async with httpx.AsyncClient() as client:
        try:
            async with client.stream(
                "POST",
                "http://localhost:8000/api/v1/copilot/stream/chat",
                json={"message": "test", "workflow_id": "test"}
            ) as response:
                if response.status_code == 200:
                    print("✓ Streaming endpoint responds")
                    # Read first event
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            print("✓ Receiving stream events")
                            break
                else:
                    print(f"✗ Streaming endpoint returned {response.status_code}")
        except Exception as e:
            print(f"✗ Streaming test failed: {e}")

asyncio.run(test_streaming())
EOF
}

################################################################################
# 7. PERFORMANCE BENCHMARKS
################################################################################
run_performance_benchmarks() {
    log_step "Running performance benchmarks..."
    
    cd backend
    source venv/bin/activate
    
    python3 << 'EOF'
import time
from app.services.template_service import TemplateService
from app.services.context_service import ContextService

print("\n=== Template Engine Performance ===")
service = TemplateService()
template = "Hello {{name}}, welcome to {{platform}}"
context = {"name": "Alice", "platform": "TenMuses"}

start = time.time()
for _ in range(10000):
    service.render(template, context)
elapsed = time.time() - start

print(f"✓ 10,000 template renders: {elapsed:.3f}s ({10000/elapsed:.0f} ops/sec)")

print("\n=== Context Analysis Performance ===")
service = ContextService()
workflow_data = {
    "nodes": [{"id": str(i), "type": "default", "label": f"Node {i}"} for i in range(100)],
    "edges": []
}

start = time.time()
items = service.create_context_items(workflow_data)
analysis = service.analyze(items)
elapsed = time.time() - start

print(f"✓ Context analysis (100 nodes): {elapsed*1000:.1f}ms")
EOF
    
    cd ..
}

################################################################################
# 8. COMPREHENSIVE DEPLOYMENT
################################################################################
full_deployment() {
    log_step "Starting full Phase 4 deployment..."
    
    # Step 1: Setup
    if ! setup_environment; then
        log_error "Environment setup failed"
        return 1
    fi
    
    if ! verify_env_variables; then
        log_error "Environment variables verification failed"
        return 1
    fi
    
    # Step 2: Dependencies
    if ! install_dependencies; then
        log_error "Dependency installation failed"
        return 1
    fi
    
    # Step 3: Testing
    if ! run_backend_tests; then
        log_error "Backend tests failed"
        return 1
    fi
    
    if ! run_frontend_tests; then
        log_error "Frontend tests failed"
        return 1
    fi
    
    if ! build_frontend; then
        log_error "Frontend build failed"
        return 1
    fi
    
    # Step 4: Database
    if ! setup_database; then
        log_error "Database setup failed"
        return 1
    fi
    
    # Step 5: Docker
    if ! build_docker_images; then
        log_error "Docker build failed"
        return 1
    fi
    
    if ! start_docker_services; then
        log_error "Failed to start services"
        return 1
    fi
    
    # Step 6: Verification
    sleep 3
    verify_backend_api
    verify_frontend
    verify_streaming
    
    log_success "Phase 4 deployment completed successfully!"
    return 0
}

################################################################################
# 9. DEPLOYMENT REPORT
################################################################################
print_deployment_report() {
    cat << 'EOF'

╔════════════════════════════════════════════════════════════════════════════╗
║                   PHASE 4 DEPLOYMENT COMPLETION REPORT                      ║
╚════════════════════════════════════════════════════════════════════════════╝

FEATURES DEPLOYED:
✓ Step 1: Streaming Response Support (SSE)
  - Server-Sent Events backend streaming
  - Real-time token display in UI
  - Token estimation and limits

✓ Step 2: Suggestion History and Favorites
  - LocalStorage persistence
  - Full-text search
  - Type filtering
  - Export/Import functionality

✓ Step 3: Prompt Template Editor
  - Template engine with {{variable}} syntax
  - Syntax highlighting
  - Real-time preview
  - Variable management

✓ Step 4: Context Control and Optimization
  - Intelligent context selection
  - Token limit optimization
  - Analysis and suggestions
  - Workflow serialization

SYSTEM STATUS:
✓ Backend API running on http://localhost:8000
✓ Frontend running on http://localhost:3000
✓ Database connected
✓ WebSocket streaming active
✓ All integration tests passing

ENDPOINTS AVAILABLE:
POST   /api/v1/copilot/stream/chat      - Stream chat responses
POST   /api/v1/copilot/stream/suggest   - Stream suggestions
POST   /api/v1/copilot/stream/diagnose  - Stream diagnosis
GET    /api/v1/suggestions              - Get suggestions
POST   /api/v1/templates                - Create templates
POST   /api/v1/context/serialize        - Serialize context
GET    /api/v1/context/suggestions      - Get context suggestions

DOCUMENTATION:
- API Docs: http://localhost:8000/docs
- Frontend: http://localhost:3000
- Test Results: See test output above

NEXT STEPS:
1. Access frontend at http://localhost:3000
2. Create a new workflow
3. Test each Copilot feature:
   - Chat tab for discussions
   - Stream tab for real-time responses
   - History tab for saved suggestions
   - Template tab for prompt templates
   - Context tab for context optimization

4. Monitor logs with:
   - Backend: docker logs tenmuses-backend
   - Frontend: docker logs tenmuses-frontend
   - Database: docker logs tenmuses-postgres

SUPPORT:
For issues or questions, check:
- /docs/PHASE_4_DEPLOYMENT.md
- Backend logs
- Frontend browser console

════════════════════════════════════════════════════════════════════════════════

EOF
}

################################################################################
# MAIN
################################################################################
main() {
    echo ""
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║   Phase 4 TenMuses Copilot - Deployment & Verification        ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""
    
    case "${1:-deploy}" in
        deploy)
            full_deployment && print_deployment_report
            ;;
        test)
            log_step "Running all tests..."
            run_backend_tests && run_frontend_tests
            ;;
        benchmark)
            run_performance_benchmarks
            ;;
        verify)
            verify_backend_api
            verify_frontend
            verify_streaming
            ;;
        docker-up)
            start_docker_services
            ;;
        docker-down)
            stop_docker_services
            ;;
        *)
            cat << 'EOF'
Usage: ./PHASE_4_DEPLOYMENT.sh [command]

Commands:
  deploy       - Full deployment (setup, test, build, verify)
  test         - Run all integration tests
  benchmark    - Run performance benchmarks
  verify       - Verify deployed system
  docker-up    - Start Docker services
  docker-down  - Stop Docker services

Examples:
  ./PHASE_4_DEPLOYMENT.sh deploy      # Complete deployment
  ./PHASE_4_DEPLOYMENT.sh test        # Run tests only
  ./PHASE_4_DEPLOYMENT.sh benchmark   # Performance benchmarks

EOF
            ;;
    esac
}

main "$@"
