#!/bin/bash
# Copilot 全功能测试脚本

API_URL="http://localhost:8000/api/v1"
EMAIL="test_copilot@test.com"
PASSWORD="testpass123"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "======================================================================"
echo "  🧪 Copilot 全功能测试"
echo "  测试所有 API 端点是否能正常从 LLM 返回数据"
echo "======================================================================"
echo ""

# 登录获取 token
echo "🔐 登录中..."
LOGIN_RESPONSE=$(curl -s -X POST "${API_URL}/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"${EMAIL}\",\"password\":\"${PASSWORD}\"}")

TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
    echo -e "${RED}❌ 登录失败${NC}"
    echo "$LOGIN_RESPONSE"
    exit 1
fi

echo -e "${GREEN}✅ 登录成功${NC}"
echo ""

# 计数器
TOTAL=0
SUCCESS=0
FALLBACK=0
CONFIG_ERROR=0
ERROR=0

# 测试函数
test_endpoint() {
    local name=$1
    local endpoint=$2
    local data=$3
    
    echo "======================================================================"
    echo "  测试: $name"
    echo "======================================================================"
    echo ""
    echo "📤 发送请求到: $endpoint"
    
    RESPONSE=$(curl -s -X POST "${API_URL}${endpoint}" \
      -H "Authorization: Bearer ${TOKEN}" \
      -H "Content-Type: application/json" \
      -d "$data" \
      --max-time 60)
    
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "${API_URL}${endpoint}" \
      -H "Authorization: Bearer ${TOKEN}" \
      -H "Content-Type: application/json" \
      -d "$data" \
      --max-time 60)
    
    TOTAL=$((TOTAL + 1))
    
    if [ "$HTTP_CODE" = "200" ]; then
        # 检查是否是配置错误
        if echo "$RESPONSE" | grep -q "❌ Copilot 当前无法使用"; then
            echo -e "${RED}❌ 配置错误: LLM 未正确配置${NC}"
            echo ""
            echo "响应预览:"
            echo "$RESPONSE" | head -c 300
            CONFIG_ERROR=$((CONFIG_ERROR + 1))
        # 检查是否是回退响应
        elif echo "$RESPONSE" | grep -q "我可以帮你"; then
            echo -e "${YELLOW}⚠️  回退响应（规则模式）${NC}"
            echo ""
            echo "响应预览:"
            echo "$RESPONSE" | head -c 300
            FALLBACK=$((FALLBACK + 1))
        # 正常响应
        else
            echo -e "${GREEN}✅ 成功 (HTTP $HTTP_CODE)${NC}"
            echo ""
            echo "响应预览:"
            echo "$RESPONSE" | head -c 300
            echo "..."
            SUCCESS=$((SUCCESS + 1))
        fi
    else
        echo -e "${RED}❌ 请求失败 (HTTP $HTTP_CODE)${NC}"
        echo ""
        echo "错误响应:"
        echo "$RESPONSE" | head -c 300
        ERROR=$((ERROR + 1))
    fi
    
    echo ""
    echo ""
}

# 测试 1: 聊天功能
test_endpoint "聊天功能" "/copilot/chat" '{
  "message": "什么是 LangGraph？请用一句话简短回答。",
  "model": "local-smart",
  "context": {},
  "chat_history": []
}'

# 测试 2: 工作流建议
test_endpoint "工作流建议" "/copilot/suggest/workflow" '{
  "description": "处理用户反馈的工作流",
  "complexity": "medium",
  "model": "local-smart"
}'

# 测试 3: 节点建议
test_endpoint "节点建议" "/copilot/suggest/node" '{
  "context": "需要一个处理 JSON 数据的节点",
  "previous_node_type": "Input",
  "model": "local-smart"
}'

# 测试 4: 工作流诊断
test_endpoint "工作流诊断" "/copilot/diagnose" '{
  "nodes": [
    {"id": "node1", "type": "Start", "label": "开始"},
    {"id": "node2", "type": "Tool", "label": "处理"},
    {"id": "node3", "type": "End", "label": "结束"},
    {"id": "node4", "type": "Tool", "label": "孤立节点"}
  ],
  "edges": [
    {"from": "node1", "to": "node2"},
    {"from": "node2", "to": "node3"}
  ],
  "model": "local-smart"
}'

# 测试 5: 提示词生成
test_endpoint "提示词生成" "/copilot/generate-prompt" '{
  "description": "生成一个总结长文本的提示词",
  "style": "structured",
  "model": "local-smart"
}'

# 打印总结
echo "======================================================================"
echo "  测试总结"
echo "======================================================================"
echo ""
echo "总测试数: $TOTAL"
echo -e "${GREEN}✅ 成功（LLM 正常响应）: $SUCCESS${NC}"
echo -e "${YELLOW}⚠️  回退响应（规则模式）: $FALLBACK${NC}"
echo -e "${RED}❌ 配置错误: $CONFIG_ERROR${NC}"
echo -e "${RED}❌ 其他错误: $ERROR${NC}"
echo ""
echo "----------------------------------------------------------------------"

if [ $CONFIG_ERROR -gt 0 ]; then
    echo ""
    echo -e "${YELLOW}⚠️  检测到配置错误！${NC}"
    echo ""
    echo "请确保:"
    echo "  1. 数据库中已配置 llm_providers（包含有效的 API key）"
    echo "  2. 数据库中已配置 llm_models"
    echo "  3. provider 和 model 都是 is_active = true"
    echo ""
    echo "检查配置:"
    echo "  curl ${API_URL}/llm-provider-model/providers"
    echo "  curl ${API_URL}/llm-provider-model/models"
elif [ $FALLBACK -gt 0 ]; then
    echo ""
    echo -e "${YELLOW}⚠️  部分响应使用了回退模式（规则响应）${NC}"
    echo "这可能意味着 LLM 调用失败，请检查:"
    echo "  - API key 是否有效"
    echo "  - 网络连接是否正常"
    echo "  - 后端日志中是否有错误"
elif [ $SUCCESS -eq $TOTAL ]; then
    echo ""
    echo -e "${GREEN}🎉 所有测试通过！Copilot 功能正常，模型返回数据正常！${NC}"
else
    echo ""
    echo -e "${YELLOW}⚠️  部分测试失败，请检查错误详情${NC}"
fi

echo ""
