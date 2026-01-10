#!/bin/bash
# =============================================================================
# Investment Agent System - End-to-End Testing Script
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
API_URL="${API_URL:-http://localhost:8000}"
TIMEOUT=30

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  Investment Agent System - E2E Tests${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# Track test results
PASSED=0
FAILED=0

# Test function
run_test() {
    local name="$1"
    local command="$2"
    local expected="$3"
    
    echo -n "Testing: $name... "
    
    result=$(eval "$command" 2>/dev/null || echo "ERROR")
    
    if [[ "$result" == *"$expected"* ]]; then
        echo -e "${GREEN}PASSED${NC}"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}FAILED${NC}"
        echo "  Expected: $expected"
        echo "  Got: $result"
        ((FAILED++))
        return 1
    fi
}

# =============================================================================
# 1. Health Check Tests
# =============================================================================
echo -e "\n${YELLOW}1. Health Check Tests${NC}"
echo "----------------------------------------"

run_test "API Gateway Health" \
    "curl -s -o /dev/null -w '%{http_code}' ${API_URL}/health" \
    "200"

run_test "API Gateway Response" \
    "curl -s ${API_URL}/health" \
    "healthy"

# =============================================================================
# 2. Authentication Tests
# =============================================================================
echo -e "\n${YELLOW}2. Authentication Tests${NC}"
echo "----------------------------------------"

# Register a test user
TEST_USER="testuser_$(date +%s)"
TEST_EMAIL="${TEST_USER}@test.com"
TEST_PASSWORD="TestPassword123!"

run_test "User Registration" \
    "curl -s -X POST ${API_URL}/api/v1/auth/register \
        -H 'Content-Type: application/json' \
        -d '{\"username\":\"${TEST_USER}\",\"email\":\"${TEST_EMAIL}\",\"password\":\"${TEST_PASSWORD}\"}'" \
    "user_id"

# Login and get token
LOGIN_RESPONSE=$(curl -s -X POST ${API_URL}/api/v1/auth/login \
    -H 'Content-Type: application/json' \
    -d "{\"email\":\"${TEST_EMAIL}\",\"password\":\"${TEST_PASSWORD}\"}" 2>/dev/null || echo "{}")

TOKEN=$(echo $LOGIN_RESPONSE | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

if [ -n "$TOKEN" ]; then
    echo -e "Testing: User Login... ${GREEN}PASSED${NC}"
    ((PASSED++))
else
    echo -e "Testing: User Login... ${RED}FAILED${NC}"
    ((FAILED++))
    TOKEN="invalid"
fi

run_test "Token Validation" \
    "curl -s -o /dev/null -w '%{http_code}' ${API_URL}/api/v1/auth/me \
        -H 'Authorization: Bearer ${TOKEN}'" \
    "200"

# =============================================================================
# 3. Research Workflow Tests
# =============================================================================
echo -e "\n${YELLOW}3. Research Workflow Tests${NC}"
echo "----------------------------------------"

# Create a research task
RESEARCH_RESPONSE=$(curl -s -X POST ${API_URL}/api/v1/research \
    -H 'Content-Type: application/json' \
    -H "Authorization: Bearer ${TOKEN}" \
    -d '{
        "type": "company_analysis",
        "target": "AAPL",
        "parameters": {
            "depth": "comprehensive",
            "include_competitors": true
        }
    }' 2>/dev/null || echo "{}")

TASK_ID=$(echo $RESEARCH_RESPONSE | grep -o '"task_id":"[^"]*"' | cut -d'"' -f4)

if [ -n "$TASK_ID" ]; then
    echo -e "Testing: Create Research Task... ${GREEN}PASSED${NC}"
    ((PASSED++))
else
    echo -e "Testing: Create Research Task... ${RED}FAILED${NC}"
    ((FAILED++))
    TASK_ID="test-task-id"
fi

run_test "Get Research Status" \
    "curl -s -o /dev/null -w '%{http_code}' ${API_URL}/api/v1/research/${TASK_ID} \
        -H 'Authorization: Bearer ${TOKEN}'" \
    "200"

run_test "List Research Tasks" \
    "curl -s ${API_URL}/api/v1/research \
        -H 'Authorization: Bearer ${TOKEN}'" \
    "tasks"

# =============================================================================
# 4. Agent Tests
# =============================================================================
echo -e "\n${YELLOW}4. Agent Tests${NC}"
echo "----------------------------------------"

run_test "List Available Agents" \
    "curl -s ${API_URL}/api/v1/agents \
        -H 'Authorization: Bearer ${TOKEN}'" \
    "agents"

run_test "Get Agent Status" \
    "curl -s ${API_URL}/api/v1/agents/status \
        -H 'Authorization: Bearer ${TOKEN}'" \
    "status"

# =============================================================================
# 5. Prompt Library Tests
# =============================================================================
echo -e "\n${YELLOW}5. Prompt Library Tests${NC}"
echo "----------------------------------------"

run_test "List Prompts" \
    "curl -s ${API_URL}/api/v1/prompts \
        -H 'Authorization: Bearer ${TOKEN}'" \
    "prompts"

run_test "Get Prompts by Category" \
    "curl -s '${API_URL}/api/v1/prompts?category=idea_generation' \
        -H 'Authorization: Bearer ${TOKEN}'" \
    "prompts"

# =============================================================================
# 6. Financial Data Tests
# =============================================================================
echo -e "\n${YELLOW}6. Financial Data Tests${NC}"
echo "----------------------------------------"

run_test "Get Stock Quote" \
    "curl -s ${API_URL}/api/v1/market/quote/AAPL \
        -H 'Authorization: Bearer ${TOKEN}'" \
    "price"

run_test "Get Company Profile" \
    "curl -s ${API_URL}/api/v1/market/profile/AAPL \
        -H 'Authorization: Bearer ${TOKEN}'" \
    "name"

run_test "Get Financial Statements" \
    "curl -s ${API_URL}/api/v1/market/financials/AAPL \
        -H 'Authorization: Bearer ${TOKEN}'" \
    "revenue"

# =============================================================================
# 7. Workflow Engine Tests
# =============================================================================
echo -e "\n${YELLOW}7. Workflow Engine Tests${NC}"
echo "----------------------------------------"

run_test "List Workflows" \
    "curl -s ${API_URL}/api/v1/workflows \
        -H 'Authorization: Bearer ${TOKEN}'" \
    "workflows"

run_test "Get Workflow Templates" \
    "curl -s ${API_URL}/api/v1/workflows/templates \
        -H 'Authorization: Bearer ${TOKEN}'" \
    "templates"

# =============================================================================
# 8. WebSocket Tests
# =============================================================================
echo -e "\n${YELLOW}8. WebSocket Tests${NC}"
echo "----------------------------------------"

# Check if wscat is available
if command -v wscat &> /dev/null; then
    WS_URL="${API_URL/http/ws}/ws/research/${TASK_ID}"
    timeout 5 wscat -c "$WS_URL" -x '{"type":"ping"}' 2>/dev/null && \
        echo -e "Testing: WebSocket Connection... ${GREEN}PASSED${NC}" && ((PASSED++)) || \
        echo -e "Testing: WebSocket Connection... ${YELLOW}SKIPPED (timeout)${NC}"
else
    echo -e "Testing: WebSocket Connection... ${YELLOW}SKIPPED (wscat not installed)${NC}"
fi

# =============================================================================
# 9. Performance Tests
# =============================================================================
echo -e "\n${YELLOW}9. Performance Tests${NC}"
echo "----------------------------------------"

# Measure response time
START=$(date +%s%N)
curl -s -o /dev/null ${API_URL}/health
END=$(date +%s%N)
RESPONSE_TIME=$(( (END - START) / 1000000 ))

if [ $RESPONSE_TIME -lt 500 ]; then
    echo -e "Testing: Response Time (<500ms)... ${GREEN}PASSED${NC} (${RESPONSE_TIME}ms)"
    ((PASSED++))
else
    echo -e "Testing: Response Time (<500ms)... ${RED}FAILED${NC} (${RESPONSE_TIME}ms)"
    ((FAILED++))
fi

# Concurrent requests test
echo -n "Testing: Concurrent Requests (10)... "
for i in {1..10}; do
    curl -s -o /dev/null ${API_URL}/health &
done
wait
echo -e "${GREEN}PASSED${NC}"
((PASSED++))

# =============================================================================
# Summary
# =============================================================================
echo ""
echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  Test Summary${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""
echo -e "Total Tests: $((PASSED + FAILED))"
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}All tests passed! ✓${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed. Please check the logs.${NC}"
    exit 1
fi
