# 前端快速启动指南

## 📌 前置要求

后端服务器已验证完成并运行在 `127.0.0.1:8000`

- ✅ 所有后端测试通过 (17/17)
- ✅ API 端点可用
- ✅ CORS 配置完成
- ✅ 数据库连接正常

## 🚀 前端启动步骤

### 1. 进入前端目录
```bash
cd /Users/mg/Workspace/TenMuses/frontend
```

### 2. 检查或安装依赖
```bash
npm install
```

### 3. 检查环境变量
创建或验证 `.env.local` 文件:
```bash
cat .env.local
```

应该包含:
```
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000/api/v1
NEXT_PUBLIC_WS_URL=ws://127.0.0.1:8000
```

如果不存在，从示例创建:
```bash
cp .env.local.example .env.local
```

然后编辑 `.env.local` 设置正确的 API 地址:
```
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000/api/v1
NEXT_PUBLIC_WS_URL=ws://127.0.0.1:8000
```

### 4. 启动开发服务器
```bash
npm run dev
```

### 5. 访问前端
打开浏览器访问: **http://localhost:3000**

---

## 🔗 前端-后端集成验证

一旦前端启动，验证这些关键功能:

### 1. 注册和登录
- [ ] 访问注册页面
- [ ] 创建新账户
- [ ] 登录新账户
- [ ] 验证 JWT 令牌保存在 localStorage

### 2. 工作流管理
- [ ] 创建新工作流
- [ ] 编辑工作流
- [ ] 查看工作流列表
- [ ] 删除工作流

### 3. Canvas 编辑器
- [ ] 拖动节点到 Canvas
- [ ] 连接节点
- [ ] 调整节点大小
- [ ] 删除节点

### 4. 实时更新
- [ ] 打开工作流执行
- [ ] 查看节点执行状态变化
- [ ] 接收流式输出

---

## 🐛 常见问题排查

### CORS 错误
如果看到 CORS 错误:
```
Access to XMLHttpRequest from origin 'http://localhost:3000' 
has been blocked by CORS policy
```

**解决方案**: 后端已配置 CORS，确保:
1. ✅ 后端运行在 `127.0.0.1:8000`
2. ✅ 前端环境变量正确指向后端
3. ✅ 清除浏览器缓存

### 认证错误
如果看到 "Invalid token":
```
{
  "detail": "Invalid authentication credentials"
}
```

**解决方案**:
1. 清除 localStorage 中的旧令牌
2. 重新登录创建新令牌
3. 检查令牌格式 (应为 "Bearer <token>")

### API 连接失败
如果 API 调用返回 503:

**解决方案**:
1. 确认后端服务器运行: `curl http://127.0.0.1:8000/docs`
2. 检查防火墙设置
3. 验证端口 8000 未被占用

### WebSocket 连接失败
如果看到 WebSocket 连接错误:

**解决方案**:
1. 确保环境变量 `NEXT_PUBLIC_WS_URL` 设置正确
2. WebSocket URL 应为 `ws://127.0.0.1:8000`（不是 `wss://`）
3. 检查网络连接

---

## 📊 后端 API 端点参考

### 认证
- `POST /api/v1/auth/register` - 用户注册
- `POST /api/v1/auth/login` - 用户登录
- `GET /api/v1/auth/me` - 获取当前用户

### 工作流
- `POST /api/v1/workflows` - 创建工作流
- `GET /api/v1/workflows` - 获取工作流列表
- `GET /api/v1/workflows/{id}` - 获取工作流详情
- `PUT /api/v1/workflows/{id}` - 更新工作流
- `DELETE /api/v1/workflows/{id}` - 删除工作流

### 工作空间
- `GET /api/v1/workspace` - 获取工作空间概览

### WebSocket
- `GET /ws/run/{thread_id}` - 工作流执行实时流

---

## 🔍 API 文档

实时 API 文档在: **http://127.0.0.1:8000/docs**

这提供:
- ✅ 所有端点的完整文档
- ✅ 请求/响应示例
- ✅ 可以直接测试端点
- ✅ 认证令牌管理

---

## 💾 环境变量完整列表

### 前端 (.env.local)
```
# API 服务器地址
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000/api/v1

# WebSocket 地址
NEXT_PUBLIC_WS_URL=ws://127.0.0.1:8000

# 可选: 调试模式
NEXT_DEBUG=false
```

### 后端 (.env)
```
# 数据库
DATABASE_URL=postgresql://user:password@localhost/tenmuses

# LLM
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key

# 安全
JWT_SECRET_KEY=your_jwt_secret_key

# Redis
REDIS_URL=redis://localhost:6379

# 开发
DEVELOPMENT=true
```

---

## 🧪 集成测试

运行完整的集成测试套件:

```bash
# 从项目根目录
cd /Users/mg/Workspace/TenMuses/backend

# 运行 e2e 测试
python comprehensive_e2e_test.py

# 运行前端集成测试
python frontend_integration_test.py
```

预期结果:
- ✅ 12/12 e2e 测试通过
- ✅ 5/5 集成测试通过

---

## 📱 移动设备测试

在同一网络上从其他设备测试:

### 从手机/平板访问前端
1. 获取开发机器的 IP: `ifconfig | grep "inet "`
2. 访问: `http://<your-machine-ip>:3000`
3. 确保 `.env.local` 配置了可访问的后端地址

---

## ✅ 快速检查清单

启动前端前:
- [ ] 后端服务器运行中
- [ ] 数据库可访问
- [ ] Redis 连接正常
- [ ] `.env.local` 文件存在
- [ ] API URL 环境变量正确
- [ ] 依赖已安装 (`npm install`)

启动后:
- [ ] 前端在 `http://localhost:3000` 可访问
- [ ] API 请求成功 (检查浏览器网络标签)
- [ ] WebSocket 连接建立
- [ ] 登录功能工作
- [ ] 工作流操作正常

---

## 📚 更多资源

- [项目 README](../README.md)
- [后端文档](../backend/README.md)
- [架构设计](../A_COPILOT_INTEGRATION_DESIGN.md)
- [验证报告](../FINAL_BACKEND_VERIFICATION_REPORT.md)

---

**最后更新**: 2025年1月
**状态**: 🟢 后端验证完成，前端可启动
