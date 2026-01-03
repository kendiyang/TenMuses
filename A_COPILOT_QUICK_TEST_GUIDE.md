# Copilot 快速测试指南

**文档版本**: 1.0  
**最后更新**: 2026-01-02  
**状态**: Ready for Testing

---

## 目录

1. [环境设置](#环境设置)
2. [运行测试](#运行测试)
3. [API 端点测试](#api-端点测试)
4. [前端集成测试](#前端集成测试)
5. [常见问题](#常见问题)

---

## 环境设置

### 1. 后端配置

#### 方式 A: 使用现有 .env

```bash
# 检查 .env 文件中是否有以下变量
cat .env | grep -E "OPENAI|ANTHROPIC"

# 应该看到:
# OPENAI_API_KEY=sk-...
# ANTHROPIC_API_KEY=sk-ant-...
```

#### 方式 B: 设置环境变量

```bash
# 如果 .env 中没有，可以临时设置
export OPENAI_API_KEY="your-api-key-here"

# 验证
echo $OPENAI_API_KEY
```

### 2. 安装依赖

后端依赖已经在 `requirements.txt` 中：

```bash
# 验证 openai 包
cd backend
pip list | grep openai

# 应该看到: openai >= 1.0.0
```

前端没有新增依赖（使用现有的 axios）

---

## 运行测试

### 后端单元测试

#### 方式 1: 运行所有 Copilot 测试

```bash
cd backend
python -m pytest tests/test_copilot_service.py -v
```

**预期输出**:
```
tests/test_copilot_service.py::TestCopilotChat::test_chat_basic PASSED
tests/test_copilot_service.py::TestCopilotChat::test_chat_with_history PASSED
tests/test_copilot_service.py::TestCopilotChat::test_chat_with_context PASSED
tests/test_copilot_service.py::TestWorkflowSuggestion::test_suggest_workflows PASSED
...
======================== 13 passed in 2.45s ========================
```

#### 方式 2: 运行特定测试

```bash
# 只运行 Chat 测试
pytest tests/test_copilot_service.py::TestCopilotChat -v

# 只运行工作流建议测试
pytest tests/test_copilot_service.py::TestWorkflowSuggestion -v
```

#### 方式 3: 运行集成测试

```bash
python -m pytest tests/test_copilot_api.py -v
```

**预期输出**:
```
tests/test_copilot_api.py::TestCopilotAPIChat::test_chat_success PASSED
tests/test_copilot_api.py::TestCopilotAPIWorkflowSuggestion::test_suggest_workflow_success PASSED
...
======================== 20 passed in 3.12s ========================
```

#### 方式 4: 生成测试覆盖报告

```bash
# 安装 pytest-cov
pip install pytest-cov

# 生成覆盖报告
pytest tests/test_copilot_service.py --cov=app.services.copilot_service --cov-report=html

# 打开 htmlcov/index.html
open htmlcov/index.html
```

---

## API 端点测试

### 启动后端服务

```bash
cd backend

# 使用 uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 或使用 python
python -m app.main
```

**确认输出**:
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 使用 curl 测试 API

#### 1. 健康检查

```bash
curl http://localhost:8000/api/v1/copilot/health
```

**预期响应**:
```json
{
  "status": "healthy",
  "service": "copilot"
}
```

#### 2. Chat API

```bash
curl -X POST http://localhost:8000/api/v1/copilot/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "message": "你好，帮我建议一个数据处理工作流",
    "chat_history": [],
    "context": {}
  }'
```

**预期响应**:
```json
{
  "message": "根据你的需求，我建议...",
  "suggestions": null,
  "diagnostics": null
}
```

#### 3. 工作流建议 API

```bash
curl -X POST http://localhost:8000/api/v1/copilot/suggest/workflow \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "description": "创建一个新闻分类工作流",
    "complexity": "medium"
  }'
```

**预期响应**:
```json
{
  "workflows": [
    {
      "name": "新闻分类工作流",
      "description": "分类新闻文章到不同类别",
      "nodes": [
        {"type": "Start", "label": "开始", "config": {}},
        {"type": "LLM", "label": "分类", "config": {"model": "gpt-4"}},
        {"type": "End", "label": "结束", "config": {}}
      ],
      "edges": [
        {"from": "start", "to": "classify"},
        {"from": "classify", "to": "end"}
      ],
      "explanation": "这个工作流使用 LLM 进行分类..."
    }
  ]
}
```

#### 4. 节点建议 API

```bash
curl -X POST http://localhost:8000/api/v1/copilot/suggest/node \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "context": "根据分类结果进行不同处理",
    "previous_node_type": "LLM",
    "workflow_description": "新闻分类工作流"
  }'
```

**预期响应**:
```json
{
  "suggestions": [
    {
      "type": "Router",
      "label": "条件路由",
      "config": {"condition": "category == \"政治\""},
      "explanation": "用于根据分类结果路由到不同分支"
    },
    {
      "type": "Tool",
      "label": "发送通知",
      "config": {"webhook": "https://..."},
      "explanation": "用于发送处理结果"
    }
  ]
}
```

#### 5. 诊断 API

```bash
curl -X POST http://localhost:8000/api/v1/copilot/diagnose \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "nodes": [
      {"id": "start", "type": "Start"},
      {"id": "process", "type": "LLM"},
      {"id": "end", "type": "End"}
    ],
    "edges": [
      {"from": "start", "to": "process"}
    ]
  }'
```

**预期响应**:
```json
{
  "diagnostics": [
    {
      "level": "error",
      "type": "disconnected_node",
      "description": "节点 'end' 没有输入连接",
      "location": {"node_id": "end"},
      "suggestion": "添加从 'process' 到 'end' 的连接"
    }
  ],
  "score": 60,
  "summary": "工作流缺少一个连接，无法正常执行"
}
```

#### 6. 提示词生成 API

```bash
curl -X POST http://localhost:8000/api/v1/copilot/generate-prompt \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "task_description": "将新闻标题分类为政治、体育、娱乐、其他",
    "input_format": "单行新闻标题",
    "output_format": "JSON {title, category, confidence}",
    "examples": [
      {
        "input": "习近平视察环保部",
        "output": "{\"category\": \"政治\", \"confidence\": 0.95}"
      }
    ],
    "style": "structured"
  }'
```

**预期响应**:
```json
{
  "template": {
    "prompt": "你是一个新闻分类专家。\n\n任务: 将输入的新闻标题分类到以下类别之一: 政治、体育、娱乐、其他\n\n输入格式: 单行新闻标题\n输出格式: JSON {title, category, confidence}\n\n示例:\n输入: 习近平视察环保部\n输出: {\"category\": \"政治\", \"confidence\": 0.95}\n\n现在请对以下新闻进行分类:\n{{INPUT}}",
    "style": "structured",
    "estimated_tokens": 280
  }
}
```

### 获取 JWT Token

如果没有有效的 JWT token，先创建一个测试用户并登录：

```bash
# 1. 创建用户
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "copilot_test",
    "email": "copilot@test.com",
    "password": "password123"
  }'

# 2. 登录获取 token
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "copilot_test",
    "password": "password123"
  }'

# 从响应中复制 "access_token" 值，用作 YOUR_JWT_TOKEN
```

### 使用 Postman 测试

1. **导入集合**
   ```bash
   # 复制以下内容到 Postman -> Import -> Raw text
   ```

2. **创建环境变量**
   ```
   base_url: http://localhost:8000
   token: YOUR_JWT_TOKEN
   ```

3. **请求示例** (Postman format)
   ```
   POST {{base_url}}/api/v1/copilot/chat
   Authorization: Bearer {{token}}
   Content-Type: application/json
   
   {
     "message": "建议一个工作流",
     "chat_history": [],
     "context": {}
   }
   ```

---

## 前端集成测试

### 1. 开发环境设置

```bash
cd frontend

# 确保 .env.local 中有正确的 API URL
cat .env.local | grep API_URL

# 应该看到: NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 2. 启动前端开发服务器

```bash
npm run dev
```

**确认输出**:
```
> next dev
- ready started server on 0.0.0.0:3000, url: http://localhost:3000
```

### 3. 测试 Copilot Panel 组件

#### 在工作流编辑器中查看

1. 打开浏览器访问 `http://localhost:3000`
2. 导航到工作流编辑页面
3. 查看右下角的 Copilot 面板

#### 测试聊天功能

```javascript
// 在浏览器控制台测试 API 客户端
import { copilotClient } from '@/services/copilot-client'

// 测试 chat
await copilotClient.chat({
  message: '你好',
  context: {}
})

// 测试工作流建议
await copilotClient.suggestWorkflow({
  description: '数据处理',
  complexity: 'medium'
})
```

#### 测试 Hook

```javascript
// 测试 useCopilotChat Hook
import { useCopilotChat } from '@/hooks/useCopilotChat'

const { messages, sendMessage } = useCopilotChat()
await sendMessage('测试消息')
console.log(messages) // 应该看到新消息
```

### 4. UI 验收测试

**检查清单**:
- [ ] Copilot 面板在右侧显示
- [ ] 可以输入消息
- [ ] 发送按钮可点击
- [ ] AI 响应显示正确
- [ ] 快速按钮工作正常
- [ ] 清除历史按钮可用
- [ ] 展开/收起按钮响应
- [ ] 消息自动滚动
- [ ] 错误消息显示清晰

---

## 调试技巧

### 后端调试

#### 启用详细日志

```python
# 在 backend/app/main.py 中添加
import logging
logging.basicConfig(level=logging.DEBUG)

# 或在环境变量中设置
export LOG_LEVEL=DEBUG
```

#### 检查 API 请求/响应

```bash
# 使用 curl 的详细输出
curl -v -X POST http://localhost:8000/api/v1/copilot/chat ...

# 或使用 httpie
pip install httpie
http POST localhost:8000/api/v1/copilot/chat message="test"
```

#### 数据库查询调试

```python
# 在 services/copilot_service.py 中添加日志
import logging
logger = logging.getLogger(__name__)
logger.debug(f"Chat request: {message}")
```

### 前端调试

#### Chrome DevTools

1. 打开 F12 -> Network 标签
2. 监视 API 请求到 `/api/v1/copilot/*`
3. 检查请求/响应的 payload

#### 组件调试

```bash
# 安装 React DevTools
npm install -D @react-devtools/extension

# 在组件中添加日志
console.log('CopilotPanel mounted', props)
```

#### API 客户端调试

```typescript
// 在 copilot-client.ts 中添加日志
const response = await this.client.post('/copilot/chat', request)
console.log('Copilot response:', response.data)
```

---

## 常见问题

### Q1: API 返回 401 Unauthorized

**原因**: JWT token 无效或过期

**解决**:
```bash
# 重新登录获取新 token
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "password"
  }'

# 使用新 token 重试
```

### Q2: OpenAI API Error

**原因**: API key 无效或配额已用完

**解决**:
```bash
# 检查 API key
echo $OPENAI_API_KEY

# 验证 API key 有效性
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"

# 如果失败，更新 .env 中的 OPENAI_API_KEY
```

### Q3: 前端无法连接后端

**原因**: CORS 问题或后端未运行

**解决**:
```bash
# 检查后端是否运行
curl http://localhost:8000/health

# 检查 CORS 配置
# frontend/.env.local 中的 NEXT_PUBLIC_API_URL 应为 http://localhost:8000

# 如果仍然有问题，清除浏览器缓存并刷新
```

### Q4: 测试失败 - "JSON decode error"

**原因**: API 返回无效的 JSON

**解决**:
```bash
# 检查 API 响应的原始内容
curl -X POST http://localhost:8000/api/v1/copilot/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"test"}' 2>&1 | jq .

# 检查服务器日志中的错误信息
```

### Q5: 性能问题 - API 响应缓慢

**原因**: OpenAI API 调用延迟

**解决**:
- 通常需要 3-5 秒，这是正常的
- 可以在 UI 中显示 "正在思考..." 加载状态
- 对于生产环境，考虑添加请求超时和重试逻辑

---

## 下一步

完成基础测试后，继续：

1. **Step 6: 组件集成** - 将 CopilotPanel 集成到 WorkflowCanvas
2. **Step 7: 建议卡片** - 实现工作流和节点建议的可视化
3. **Step 8: 高级功能** - 流式响应、提示词预览等

---

## 相关文档

- [设计文档](A_COPILOT_INTEGRATION_DESIGN.md)
- [实现清单](A_COPILOT_IMPLEMENTATION_CHECKLIST.md)
- [API 文档](http://localhost:8000/docs) - Swagger UI
- [后端代码](backend/app/services/copilot_service.py)
- [前端代码](frontend/src/components/workflow/CopilotPanel.tsx)

---

**版本**: 1.0  
**最后更新**: 2026-01-02  
**维护者**: TenMuses Development Team
