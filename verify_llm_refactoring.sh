#!/bin/bash

# LLM Refactoring - Post-Deployment Verification Checklist
# Run this script after deploying the refactoring changes

set -e

echo "╔═══════════════════════════════════════════════════════╗"
echo "║ LLM REFACTORING VERIFICATION CHECKLIST               ║"
echo "╚═══════════════════════════════════════════════════════╝"

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

check_count=0
pass_count=0
fail_count=0

# Helper function to print check results
check_result() {
    check_count=$((check_count + 1))
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓ PASS${NC}: $2"
        pass_count=$((pass_count + 1))
    else
        echo -e "${RED}✗ FAIL${NC}: $2"
        fail_count=$((fail_count + 1))
    fi
}

echo ""
echo "1. DATABASE VERIFICATION"
echo "─────────────────────────────────────────────────────"

# Check if psql is available
which psql > /dev/null 2>&1
check_result $? "psql command available"

# Check database connection
psql -U postgres -d tenmuses -c "SELECT 1" > /dev/null 2>&1
check_result $? "Database connection successful"

# Check if llm_providers table exists
psql -U postgres -d tenmuses -c "SELECT * FROM llm_providers LIMIT 1" > /dev/null 2>&1
check_result $? "llm_providers table exists"

# Check if llm_models table exists
psql -U postgres -d tenmuses -c "SELECT * FROM llm_models LIMIT 1" > /dev/null 2>&1
check_result $? "llm_models table exists"

# Check provider count
provider_count=$(psql -U postgres -d tenmuses -tA -c "SELECT COUNT(*) FROM llm_providers WHERE is_active=true")
if [ "$provider_count" -gt 0 ]; then
    echo -e "${GREEN}✓ PASS${NC}: Found $provider_count active providers"
    pass_count=$((pass_count + 1))
else
    echo -e "${RED}✗ FAIL${NC}: No active providers found"
    fail_count=$((fail_count + 1))
fi
check_count=$((check_count + 1))

# Check model count
model_count=$(psql -U postgres -d tenmuses -tA -c "SELECT COUNT(*) FROM llm_models WHERE is_active=true")
if [ "$model_count" -gt 0 ]; then
    echo -e "${GREEN}✓ PASS${NC}: Found $model_count active models"
    pass_count=$((pass_count + 1))
else
    echo -e "${RED}✗ FAIL${NC}: No active models found"
    fail_count=$((fail_count + 1))
fi
check_count=$((check_count + 1))

echo ""
echo "2. PYTHON ENVIRONMENT VERIFICATION"
echo "─────────────────────────────────────────────────────"

# Check if backend directory exists
if [ -d "backend" ]; then
    echo -e "${GREEN}✓ PASS${NC}: backend directory exists"
    pass_count=$((pass_count + 1))
else
    echo -e "${RED}✗ FAIL${NC}: backend directory not found"
    fail_count=$((fail_count + 1))
fi
check_count=$((check_count + 1))

# Check Python imports
cd backend
python -c "from app.models.llm_provider import LLMProvider" > /dev/null 2>&1
check_result $? "LLMProvider model imports successfully"

python -c "from app.models.llm_model import LLMModel" > /dev/null 2>&1
check_result $? "LLMModel model imports successfully"

python -c "from app.services.llm_client import llm_client" > /dev/null 2>&1
check_result $? "llm_client service imports successfully"

python -c "from app.schemas.node import LLMNodeConfig, LLMConfig" > /dev/null 2>&1
check_result $? "Schema backward compatibility alias works"

echo ""
echo "3. FILE STRUCTURE VERIFICATION"
echo "─────────────────────────────────────────────────────"

# Check if new model files exist
if [ -f "app/models/llm_provider.py" ]; then
    echo -e "${GREEN}✓ PASS${NC}: llm_provider.py exists"
    pass_count=$((pass_count + 1))
else
    echo -e "${RED}✗ FAIL${NC}: llm_provider.py not found"
    fail_count=$((fail_count + 1))
fi
check_count=$((check_count + 1))

if [ -f "app/models/llm_model.py" ]; then
    echo -e "${GREEN}✓ PASS${NC}: llm_model.py exists"
    pass_count=$((pass_count + 1))
else
    echo -e "${RED}✗ FAIL${NC}: llm_model.py not found"
    fail_count=$((fail_count + 1))
fi
check_count=$((check_count + 1))

if [ -f "app/services/llm_client.py" ]; then
    echo -e "${GREEN}✓ PASS${NC}: llm_client.py exists"
    pass_count=$((pass_count + 1))
else
    echo -e "${RED}✗ FAIL${NC}: llm_client.py not found"
    fail_count=$((fail_count + 1))
fi
check_count=$((check_count + 1))

if [ -f "app/services/llm_client_old.py" ]; then
    echo -e "${GREEN}✓ PASS${NC}: llm_client_old.py (backup) exists"
    pass_count=$((pass_count + 1))
else
    echo -e "${YELLOW}⚠ INFO${NC}: llm_client_old.py backup not found (optional)"
fi
check_count=$((check_count + 1))

if [ -f "app/scripts/migrate_llm_config_to_provider_model.py" ]; then
    echo -e "${GREEN}✓ PASS${NC}: Migration script exists"
    pass_count=$((pass_count + 1))
else
    echo -e "${RED}✗ FAIL${NC}: Migration script not found"
    fail_count=$((fail_count + 1))
fi
check_count=$((check_count + 1))

echo ""
echo "4. TEST EXECUTION VERIFICATION"
echo "─────────────────────────────────────────────────────"

# Run core workflow tests
echo "Running test_phase2_comprehensive.py..."
python -m pytest tests/test_phase2_comprehensive.py -q > /dev/null 2>&1
check_result $? "test_phase2_comprehensive.py (21 tests)"

# Run langgraph service tests
echo "Running test_langgraph_service.py..."
python -m pytest tests/test_langgraph_service.py -q > /dev/null 2>&1
check_result $? "test_langgraph_service.py (8 tests)"

# Run copilot service tests
echo "Running test_copilot_service.py..."
python -m pytest tests/test_copilot_service.py -q > /dev/null 2>&1
check_result $? "test_copilot_service.py (22 tests)"

echo ""
echo "5. API ENDPOINT VERIFICATION"
echo "─────────────────────────────────────────────────────"

# Check if config.py has the new endpoint
if grep -q "/config/llm/available-models" "app/api/v1/config.py" 2>/dev/null; then
    echo -e "${GREEN}✓ PASS${NC}: New API endpoint defined in config.py"
    pass_count=$((pass_count + 1))
else
    echo -e "${RED}✗ FAIL${NC}: API endpoint not found in config.py"
    fail_count=$((fail_count + 1))
fi
check_count=$((check_count + 1))

echo ""
echo "6. CODE QUALITY VERIFICATION"
echo "─────────────────────────────────────────────────────"

# Check if executor_library.py has been updated
if grep -q "HumanMessage" "app/services/executor_library.py" 2>/dev/null; then
    echo -e "${GREEN}✓ PASS${NC}: executor_library.py updated for new API"
    pass_count=$((pass_count + 1))
else
    echo -e "${RED}✗ FAIL${NC}: executor_library.py may not be updated"
    fail_count=$((fail_count + 1))
fi
check_count=$((check_count + 1))

# Check if dynamic_graph_factory.py has been updated
if grep -q "HumanMessage" "app/services/dynamic_graph_factory.py" 2>/dev/null; then
    echo -e "${GREEN}✓ PASS${NC}: dynamic_graph_factory.py updated for new API"
    pass_count=$((pass_count + 1))
else
    echo -e "${RED}✗ FAIL${NC}: dynamic_graph_factory.py may not be updated"
    fail_count=$((fail_count + 1))
fi
check_count=$((check_count + 1))

# Check backward compatibility alias
if grep -q "LLMConfig = LLMNodeConfig" "app/schemas/node.py" 2>/dev/null; then
    echo -e "${GREEN}✓ PASS${NC}: Schema backward compatibility alias present"
    pass_count=$((pass_count + 1))
else
    echo -e "${RED}✗ FAIL${NC}: Schema backward compatibility alias missing"
    fail_count=$((fail_count + 1))
fi
check_count=$((check_count + 1))

cd ..

echo ""
echo "╔═══════════════════════════════════════════════════════╗"
echo "║                    SUMMARY                            ║"
echo "╚═══════════════════════════════════════════════════════╝"
echo ""
echo "Total Checks:  $check_count"
echo -e "${GREEN}Passed:       $pass_count${NC}"
echo -e "${RED}Failed:       $fail_count${NC}"
echo ""

if [ $fail_count -eq 0 ]; then
    echo -e "${GREEN}╔═══════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║     ✓ ALL VERIFICATION CHECKS PASSED                  ║${NC}"
    echo -e "${GREEN}║     Refactoring is ready for production deployment    ║${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════════════════════╝${NC}"
    exit 0
else
    echo -e "${RED}╔═══════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║     ✗ SOME CHECKS FAILED                             ║${NC}"
    echo -e "${RED}║     Please review and fix the failures above          ║${NC}"
    echo -e "${RED}╚═══════════════════════════════════════════════════════╝${NC}"
    exit 1
fi
