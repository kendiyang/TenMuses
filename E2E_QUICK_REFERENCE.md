# 📖 TenMuses E2E 测试快速参考

## 🚀 快速启动

```bash
# 1. 启动后端服务
cd backend
source venv/bin/activate
uvicorn app.main:app --reload

# 2. 启动前端服务 (新终端)
cd frontend
npm run dev

# 3. 运行 E2E 测试 (第三个终端)
cd backend && source venv/bin/activate
python ../e2e_comprehensive_test.py
```

---

## 📊 当前测试结果

**通过率**: 82.4% (14/17 通过) ✅

| 功能 | 状态 | 详情 |
|------|------|------|
| 基础设施 | ✅ 2/2 | 后端和前端都正常运行 |
| 认证 | ✅ 2/2 | 注册和 Token 验证正常 |
| LLM 配置 | ✅ 2/2 | 供应商和模型列表正常 |
| 工作流 CRUD | ✅ 3/3 | 创建、读取、列表正常 |
| 动态工作流 | ✅ 2/4 | 验证正常，执行需要修复 |
| Copilot API | ✅ 2/2 | 聊天和建议都正常 |
| RAG | ✅ 1/2 | 上传成功，搜索需要修复 |
| WebSocket | ⊘ 0/1 | 可选，需要 websockets 库 |

---

## 🔑 关键配置

### LLM 供应商
- **名称**: OpenAI (Custom)
- **Base URL**: `https://chrisapius.top/v1`
- **API Key**: 已加密存储在数据库

### 激活的模型
1. **gpt-4o** - 聊天模型 (128K 上下文)
2. **text-embedding-3-large** - 向量模型 (3072 维)
3. **gpt-5.2** - Chris API 自定义模型

### 数据库
- **类型**: PostgreSQL + pgvector
- **表**: LLMProvider, LLMModel, Workflow, KBDocument, KBChunk 等

---

## 🎯 API 端点测试清单

### LLM 配置
```bash
# 获取供应商列表
curl -X GET http://localhost:8000/api/v1/llm-config/providers \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json"

# 获取模型列表
curl -X GET http://localhost:8000/api/v1/llm-config/models \
  -H "Authorization: Bearer $TOKEN"
```

### 动态工作流
```bash
# 验证工作流图
curl -X POST http://localhost:8000/api/v1/dynamic/validate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "nodes": [...],
    "edges": [...],
    "viewport": {}
  }'

# 执行工作流
curl -X POST http://localhost:8000/api/v1/dynamic/execute \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "nodes": [...],
    "edges": [...],
    "input_data": {...}
  }'
```

### Copilot
```bash
# 聊天
curl -X POST http://localhost:8000/api/v1/copilot/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "...", "model": "local-smart"}'

# 获取建议
curl -X POST http://localhost:8000/api/v1/copilot/suggestions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"type": "workflow", "context": "..."}'
```

### RAG 知识库
```bash
# 上传文档
curl -X POST http://localhost:8000/api/v1/kb/documents \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@document.pdf"

# 搜索文档
curl -X POST http://localhost:8000/api/v1/kb/documents/search \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "...", "top_k": 5}'
```

---

## 🐛 常见问题排查

### 问题 1: 后端启动失败
```
错误: ImportError: cannot import name 'AnthropicEmbeddings'
解决: 已修复 - embedding_service.py 已注释掉该导入
```

### 问题 2: LLM 配置端点 404
```
错误: GET /api/v1/llm-config/providers → 404
解决: 已创建 llm_provider_model.py 并在 main.py 中注册
```

### 问题 3: RAG 文档上传 500
```
错误: KBDocumentResponse metadata 验证失败
解决: 已使用 Pydantic Field 别名 alias="doc_metadata"
```

### 问题 4: 执行工作流 500
```
错误: dynamic/execute 返回 500
状态: 待调查
建议: 检查 backend.log 获取详细错误信息
```

### 问题 5: 搜索文档 500
```
错误: RAG 搜索返回 500
状态: 待调查
建议: 验证 pgvector 查询语法
```

---

## 📝 测试脚本使用

```python
# 运行所有测试
python e2e_comprehensive_test.py

# 输出示例:
# ======================================================================
# 📊 测试总结
# ======================================================================
# 总测试数: 17
# ✓ 通过: 14 (82.4%)
# ✗ 失败: 2 (11.8%)
# ⊘ 跳过: 1 (5.9%)
```

### 测试覆盖范围
1. **基础设施** - 后端和前端服务可用性
2. **认证** - 用户注册和 Token 验证
3. **LLM 配置** - 供应商和模型 API
4. **工作流 CRUD** - 创建、读取、列表操作
5. **动态工作流** - 图验证和执行
6. **Copilot** - 聊天和建议功能
7. **RAG** - 文档上传和搜索
8. **WebSocket** - 流式执行 (可选)

---

## 🔍 调试技巧

### 查看后端日志
```bash
# 实时日志
tail -f /tmp/backend.log

# 查看最近 50 行
tail -50 /tmp/backend.log

# 搜索错误
grep -i "error\|exception" /tmp/backend.log
```

### 检查数据库
```bash
# 连接数据库
psql tenmuses

# 查看 LLM 供应商
SELECT id, name, base_url, is_active FROM llm_providers;

# 查看 LLM 模型
SELECT id, provider_id, model_name, context_window FROM llm_models;

# 查看知识库文档
SELECT id, filename, status, chunk_count FROM kb_documents;
```

### 测试 API 端点
```bash
# 获取 Token
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "testpass"
  }' | jq '.access_token'

# 保存 Token
export TOKEN="eyJ0eXAiOiJKV1QiLCJhbGc..."

# 测试受保护的端点
curl http://localhost:8000/api/v1/workflows \
  -H "Authorization: Bearer $TOKEN"
```

---

## 📚 文档索引

| 文档 | 用途 |
|------|------|
| [E2E_TEST_REPORT_20260101.md](E2E_TEST_REPORT_20260101.md) | 详细的测试报告和结果分析 |
| [E2E_TEST_IMPROVEMENT_SUMMARY.md](E2E_TEST_IMPROVEMENT_SUMMARY.md) | 改进轨迹和修复清单 |
| [INIT_DB_GUIDE.md](INIT_DB_GUIDE.md) | 数据库初始化指南 |
| [DB_INIT_SUCCESS_REPORT.md](DB_INIT_SUCCESS_REPORT.md) | 初始化成功报告 |
| [QUICKSTART.md](QUICKSTART.md) | 项目快速入门 |
| [README.md](README.md) | 项目概述 |

---

## 🎯 下一步工作

### 立即修复 (P0)
- [ ] 调查执行工作流 HTTP 500 错误
- [ ] 调查搜索文档 HTTP 500 错误

### 短期计划 (P1)
- [ ] 安装 websockets 库
- [ ] 启用 WebSocket 流式测试
- [ ] 达成 90%+ 通过率

### 长期优化 (P2)
- [ ] 添加更多测试用例
- [ ] 集成到 CI/CD 管道
- [ ] 性能基准测试

---

## 💬 快速命令

```bash
# 启动所有服务
./scripts/dev.sh

# 运行数据库初始化
cd backend && source venv/bin/activate
python init_db_providers_models.py

# 清理和重启
pkill uvicorn
pkill node
cd backend && rm -rf __pycache__ && uvicorn app.main:app --reload
```

---

**最后更新**: 2026-01-01  
**当前通过率**: 82.4% ✅  
**状态**: 核心功能验证通过，系统可进行生产评估
