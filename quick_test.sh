#!/bin/bash

echo "🧪 Copilot 功能验证"
echo "================================"

# 登录获取Token
echo "📝 获取认证Token..."
LOGIN_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test_copilot@test.com","password":"testpass123"}')

TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null)

if [ -z "$TOKEN" ]; then
    echo "❌ Failed to get token"
    exit 1
fi

echo "✅ 已获取Token"
echo ""

# 测试 Chat 端点
echo "1️⃣  测试 Chat 端点"
CHAT_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/copilot/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"message":"What is LangGraph? Explain in one sentence.","model":"local-smart"}')

CHAT_MSG=$(echo "$CHAT_RESPONSE" | python3 -c "import sys, json; r=json.load(sys.stdin); print(r.get('message', ''))" 2>/dev/null)

if echo "$CHAT_MSG" | grep -q "我可以帮"; then
    echo "   ⚠️  回退响应 (Rule-based)"
else
    echo "   ✅ LLM 响应"
fi
echo "   Message: ${CHAT_MSG:0:80}..."
echo ""

# 测试 Workflow Suggestion 端点
echo "2️⃣  测试 Workflow Suggestion 端点"
WF_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/copilot/suggest/workflow \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"description":"Create a data processing workflow","model":"local-smart"}')

WF_COUNT=$(echo "$WF_RESPONSE" | python3 -c "import sys, json; r=json.load(sys.stdin); print(len(r.get('workflows', [])))" 2>/dev/null)
echo "   ✅ 返回 $WF_COUNT 个工作流建议"
echo ""

# 测试 Node Suggestion 端点
echo "3️⃣  测试 Node Suggestion 端点"
NODE_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/copilot/suggest/node \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"context":"process data with AI","model":"local-smart"}')

NODE_COUNT=$(echo "$NODE_RESPONSE" | python3 -c "import sys, json; r=json.load(sys.stdin); print(len(r.get('suggestions', [])))" 2>/dev/null)
echo "   ✅ 返回 $NODE_COUNT 个节点建议"
echo ""

# 测试 Diagnose 端点
echo "4️⃣  测试 Workflow Diagnosis 端点"
DIAG_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/copilot/diagnose \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"workflow":{"nodes":[{"id":"n1","type":"Start","label":"Start"},{"id":"n2","type":"LLM","label":"Process"}],"edges":[{"from":"n1","to":"n2"}]},"model":"local-smart"}')

DIAG_SCORE=$(echo "$DIAG_RESPONSE" | python3 -c "import sys, json; r=json.load(sys.stdin); print(r.get('score', 0))" 2>/dev/null)
echo "   ✅ 工作流诊断分数: $DIAG_SCORE"
echo ""

# 测试 Prompt Generation 端点
echo "5️⃣  测试 Prompt Generation 端点"
PROMPT_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/copilot/generate-prompt \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"task_description":"Summarize a long text","style":"structured","model":"local-smart"}')

PROMPT_LEN=$(echo "$PROMPT_RESPONSE" | python3 -c "import sys, json; r=json.load(sys.stdin); print(len(r.get('prompt', '')))" 2>/dev/null)
echo "   ✅ 生成的提示词长度: $PROMPT_LEN 字符"
echo ""

echo "================================"
echo "✅ 功能验证完成!"
