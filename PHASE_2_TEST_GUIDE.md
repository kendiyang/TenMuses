# Phase 2 快速测试指南

## 🚀 快速开始

### 1. 运行独立测试（推荐）

```bash
cd backend
source ../.venv/bin/activate
python test_phase2_standalone.py
```

**预期输出**: ✅ 所有测试通过 8/8 (100.0%)

### 2. 运行Pytest测试套件

```bash
cd backend
source ../.venv/bin/activate
pytest tests/test_phase2_comprehensive.py -v
```

### 3. 测试API端点

```bash
# 启动后端服务
cd backend
source ../.venv/bin/activate
python -m app.main

# 新终端测试
curl http://localhost:8000/api/v1/dynamic/tools | jq
curl http://localhost:8000/api/v1/dynamic/templates | jq
```

---

## 📊 测试覆盖总览

### 独立测试 (test_phase2_standalone.py)

| 测试名称 | 状态 | 说明 |
|---------|------|------|
| 节点创建 | ✅ | LLM和Tool节点 |
| 图验证 | ✅ | 3节点线性工作流 |
| 重复节点检测 | ✅ | 错误处理 |
| 无效边检测 | ✅ | 错误处理 |
| 工厂创建 | ✅ | 执行器构建 |
| 工具库 | ✅ | 3个内置工具 |
| 表达式评估器 | ✅ | 条件路由 |
| 大型工作流 | ✅ | 100节点性能 |

### Pytest测试套件 (test_phase2_comprehensive.py)

**7个测试类**:
- `TestBasicFunctionality` - 基础功能
- `TestErrorHandling` - 错误处理
- `TestEdgeCases` - 边界情况
- `TestConditionalRouting` - 条件路由
- `TestPerformance` - 性能测试
- `TestExecutors` - 执行器测试
- `TestIntegration` - 集成测试

---

## 🔧 常见问题

### Q: 测试失败 "ModuleNotFoundError: No module named 'app'"

**A**: 确保从backend目录运行测试：
```bash
cd backend && python test_phase2_standalone.py
```

### Q: 如何只运行特定测试？

**A**: 使用pytest的-k选项：
```bash
pytest tests/test_phase2_comprehensive.py -k "test_node_creation"
```

### Q: 如何查看详细输出？

**A**: 添加-v和--capture=no：
```bash
pytest tests/test_phase2_comprehensive.py -v --capture=no
```

---

## 📈 性能基准

| 指标 | 当前值 | 目标 | 状态 |
|------|--------|------|------|
| 100节点编译 | 0.0001秒 | < 1秒 | ✅ |
| 单节点验证 | < 0.001秒 | < 0.01秒 | ✅ |
| 工具执行 | < 0.01秒 | < 0.1秒 | ✅ |

---

## 🎯 下一步

1. **修复P0问题**: 安全性、重试、速率限制
2. **运行完整集成测试**: WebSocket + HITL
3. **Beta测试**: 真实场景验证

---

更多详情请查看:
- [PHASE_2_CODE_REVIEW.md](PHASE_2_CODE_REVIEW.md) - 完整代码审查
- [PHASE_2_REVIEW_SUMMARY.md](PHASE_2_REVIEW_SUMMARY.md) - 审查总结
