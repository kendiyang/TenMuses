#!/usr/bin/env bash

##############################################################################
# 前后端集成测试脚本
# 测试前端与后端 API 的真实交互
##############################################################################

set -e

# 配置
BACKEND_URL="http://localhost:8000"
BACKEND_API="${BACKEND_URL}/api/v1"
FRONTEND_URL="http://localhost:3000"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 测试结果统计
PASSED=0
FAILED=0

# 辅助函数：打印标题
print_header() {
  echo -e "\n${BLUE}========== $1 ==========${NC}\n"
}

# 辅助函数：打印测试结果
print_test() {
  local test_name=$1
  local status=$2
  
  if [ "$status" = "PASS" ]; then
    echo -e "${GREEN}✓${NC} $test_name"
    ((PASSED++))
  else
    echo -e "${RED}✗${NC} $test_name"
    ((FAILED++))
  fi
}

# 辅助函数：测试 API 端点
test_api_endpoint() {
  local method=$1
  local endpoint=$2
  local data=$3
  local expected_status=$4
  
  if [ "$method" = "GET" ]; then
    response=$(curl -s -w "\n%{http_code}" \
      -H "Content-Type: application/json" \
      "${BACKEND_API}${endpoint}")
  else
    response=$(curl -s -w "\n%{http_code}" \
      -X "$method" \
      -H "Content-Type: application/json" \
      -d "$data" \
      "${BACKEND_API}${endpoint}")
  fi
  
  http_code=$(echo "$response" | tail -n 1)
  body=$(echo "$response" | sed '$d')
  
  if [[ "$http_code" == "$expected_status"* ]]; then
    return 0
  else
    echo "  Expected: $expected_status, Got: $http_code"
    echo "  Response: $body"
    return 1
  fi
}

##############################################################################
# 测试 1: 后端健康检查
##############################################################################
print_header "后端健康检查"

if test_api_endpoint "GET" "/health" "" "200"; then
  print_test "后端服务运行中" "PASS"
else
  print_test "后端服务运行中" "FAIL"
  echo -e "${RED}错误：后端服务未运行。请先启动后端服务：${NC}"
  echo "  cd backend && uvicorn app.main:app --reload"
  exit 1
fi

##############################################################################
# 测试 2: Copilot 聊天 API
##############################################################################
print_header "Copilot 聊天 API"

chat_payload='{"message":"Hello, help me create a workflow","chat_history":[]}'
if test_api_endpoint "POST" "/copilot/chat" "$chat_payload" "200"; then
  print_test "聊天消息发送" "PASS"
else
  print_test "聊天消息发送" "FAIL"
fi

# 测试带历史的聊天
chat_history_payload='{"message":"继续","chat_history":[{"role":"user","content":"hello"},{"role":"assistant","content":"hi"}]}'
if test_api_endpoint "POST" "/copilot/chat" "$chat_history_payload" "200"; then
  print_test "聊天历史处理" "PASS"
else
  print_test "聊天历史处理" "FAIL"
fi

##############################################################################
# 测试 3: 工作流建议 API
##############################################################################
print_header "工作流建议 API"

workflow_suggest_payload='{"description":"Create a RAG workflow","complexity":"medium"}'
if test_api_endpoint "POST" "/copilot/suggest-workflows" "$workflow_suggest_payload" "200"; then
  print_test "工作流建议生成" "PASS"
else
  print_test "工作流建议生成" "FAIL"
fi

##############################################################################
# 测试 4: 节点建议 API
##############################################################################
print_header "节点建议 API"

node_suggest_payload='{"context":"I need to process documents","previous_node_type":"LLM","workflow_description":"Document processing"}'
if test_api_endpoint "POST" "/copilot/suggest-nodes" "$node_suggest_payload" "200"; then
  print_test "节点建议生成" "PASS"
else
  print_test "节点建议生成" "FAIL"
fi

##############################################################################
# 测试 5: 工作流诊断 API
##############################################################################
print_header "工作流诊断 API"

diagnose_payload='{"workflow":{"nodes":[{"id":"1","type":"Start","label":"Start"}],"edges":[]}}'
if test_api_endpoint "POST" "/copilot/diagnose-workflow" "$diagnose_payload" "200"; then
  print_test "工作流诊断" "PASS"
else
  print_test "工作流诊断" "FAIL"
fi

##############################################################################
# 测试 6: 提示词生成 API
##############################################################################
print_header "提示词生成 API"

prompt_payload='{"task_description":"Summarize documents","input_format":"text","output_format":"json"}'
if test_api_endpoint "POST" "/copilot/generate-prompt" "$prompt_payload" "200"; then
  print_test "提示词模板生成" "PASS"
else
  print_test "提示词模板生成" "FAIL"
fi

##############################################################################
# 测试 7: 建议历史 API
##############################################################################
print_header "建议历史 API"

suggestion_payload='{"type":"workflow","content":"Suggested workflow","metadata":{"description":"Test"}}'
if test_api_endpoint "POST" "/suggestions" "$suggestion_payload" "20"; then
  print_test "建议保存" "PASS"
else
  print_test "建议保存" "FAIL"
fi

# 测试获取建议列表
if test_api_endpoint "GET" "/suggestions" "" "200"; then
  print_test "建议列表获取" "PASS"
else
  print_test "建议列表获取" "FAIL"
fi

##############################################################################
# 测试 8: 模板 API
##############################################################################
print_header "模板管理 API"

template_payload='{"name":"Test Template","description":"A test","content":"Hello {{name}}","variables":["name"]}'
if test_api_endpoint "POST" "/templates" "$template_payload" "20"; then
  print_test "模板保存" "PASS"
else
  print_test "模板保存" "FAIL"
fi

if test_api_endpoint "GET" "/templates" "" "200"; then
  print_test "模板列表获取" "PASS"
else
  print_test "模板列表获取" "FAIL"
fi

##############################################################################
# 测试 9: 上下文管理 API
##############################################################################
print_header "上下文管理 API"

context_payload='{"nodes":[{"id":"1","type":"LLM","label":"Process"}],"edges":[]}'
if test_api_endpoint "POST" "/context/analyze" "$context_payload" "200"; then
  print_test "上下文分析" "PASS"
else
  print_test "上下文分析" "FAIL"
fi

##############################################################################
# 前端 TypeScript 类型检查
##############################################################################
print_header "前端类型检查"

cd "${SCRIPT_DIR}/../frontend" 2>/dev/null || cd "./frontend" 2>/dev/null || true

if command -v npm &> /dev/null; then
  if npm run type-check --silent 2>/dev/null | head -1 | grep -q "error"; then
    print_test "前端 TypeScript 检查" "FAIL"
  else
    print_test "前端 TypeScript 检查" "PASS"
  fi
else
  echo -e "${YELLOW}⚠${NC}  npm 未安装，跳过前端检查"
fi

##############################################################################
# 测试总结
##############################################################################
print_header "测试总结"

TOTAL=$((PASSED + FAILED))
PASS_RATE=$((PASSED * 100 / TOTAL))

echo "总计: $TOTAL 个测试"
echo -e "${GREEN}✓ 通过: $PASSED${NC}"
echo -e "${RED}✗ 失败: $FAILED${NC}"
echo -e "通过率: ${PASS_RATE}%\n"

if [ $FAILED -eq 0 ]; then
  echo -e "${GREEN}✓ 所有测试通过！前后端集成正常。${NC}"
  exit 0
else
  echo -e "${RED}✗ 有 $FAILED 个测试失败。请检查上面的错误信息。${NC}"
  exit 1
fi
