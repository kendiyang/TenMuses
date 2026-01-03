# 🚀 TenMuses 快速测试指南
**版本**: v2.3.0  
**更新日期**: 2026-01-03

---

## 📋 测试清单

### ✅ Task 22: 头像上传功能

#### 后端测试
```bash
# 1. 启动后端服务
cd backend
python -m app.main

# 2. 检查静态文件目录是否创建
ls uploads/avatars  # 应该存在

# 3. 测试上传端点（需要 token）
curl -X POST "http://localhost:8000/api/v1/users/me/avatar" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@/path/to/image.jpg"

# 4. 查看上传的文件
ls uploads/avatars

# 5. 访问头像（浏览器）
http://localhost:8000/uploads/avatars/FILENAME.jpg
```

#### 前端测试
```bash
# 1. 启动前端
cd frontend
npm run dev

# 2. 访问资料页面
http://localhost:3000/profile

# 3. 测试功能
✓ 点击 "Upload Avatar" 按钮
✓ 选择一张图片（JPG/PNG/GIF/WebP）
✓ 查看实时预览
✓ 确认上传成功
✓ 点击右上角 X 按钮删除头像
✓ 尝试上传超过 5MB 的文件（应该失败）
✓ 尝试上传非图片文件（应该失败）
```

**预期结果**:
- ✅ 头像立即显示预览
- ✅ 上传进度有加载指示器
- ✅ 上传成功后显示新头像
- ✅ 文件验证错误有提示
- ✅ 删除功能正常工作

---

### ✅ Task 25: 分页组件

#### 后端测试
```bash
# 1. 测试分页 API（需要 token）
curl "http://localhost:8000/api/v1/marketplace/templates?page=1&page_size=10" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 2. 验证响应格式
# 应该包含：
# - items: 模板数组
# - total: 总数量
# - page: 当前页
# - page_size: 每页大小
# - total_pages: 总页数
```

#### 前端测试
```bash
# 1. 访问 Marketplace
http://localhost:3000/marketplace

# 2. 测试分页功能
✓ 查看页面底部的分页组件
✓ 点击页码按钮切换页面
✓ 点击 "First page" 按钮（最左边）
✓ 点击 "Last page" 按钮（最右边）
✓ 点击 "Previous" 和 "Next" 按钮
✓ 改变每页显示数量（12/24/48/96）
✓ 查看数据范围提示（Showing X to Y of Z results）
✓ 确认禁用状态（首页时Previous禁用，末页时Next禁用）
```

**预期结果**:
- ✅ 页面切换时数据自动刷新
- ✅ 页码按钮有当前页高亮
- ✅ 省略号显示正确（页数 > 7）
- ✅ 每页大小改变时回到第1页
- ✅ 数据范围计算正确

---

### ✅ Task 23: WebSocket 执行流测试

#### 方法1: Python 自动化测试
```bash
# 1. 确保后端运行
cd backend
python -m app.main

# 2. 在另一个终端运行测试
cd /Users/mg/Workspace/TenMuses
python test_websocket_execution.py

# 3. 查看测试输出
# 应该看到彩色的日志输出和事件流
```

**预期输出**:
```
[HH:MM:SS] Registering test user: test_ws_xxxxx@example.com
[HH:MM:SS] ✓ User registered successfully
[HH:MM:SS] Creating test workflow...
[HH:MM:SS] ✓ Workflow created: workflow-id
[HH:MM:SS] Testing WebSocket execution for workflow: workflow-id
[HH:MM:SS] ← Event: connected
[HH:MM:SS] → Sending start action...
[HH:MM:SS] ← Event: run_started
[HH:MM:SS] ← Event: node_started
[HH:MM:SS] ← Event: token
[HH:MM:SS] ← Event: run_completed
[HH:MM:SS] 
=== Test Results ===
[HH:MM:SS] Events received: 5
[HH:MM:SS] Event types: connected, run_started, node_started, token, run_completed
[HH:MM:SS] Execution started: True
[HH:MM:SS] Execution completed: True
[HH:MM:SS] 
✓ TEST PASSED: WebSocket execution flow working correctly
```

#### 方法2: 前端测试页面
```bash
# 1. 访问测试页面
http://localhost:3000/test-websocket

# 2. 测试流程
✓ 点击 "Connect" 按钮
✓ 确认连接状态变为绿色
✓ 点击 "Start Execution" 按钮
✓ 观察左侧事件日志
✓ 观察右侧执行输出
✓ 等待执行完成
✓ 点击 "Disconnect" 断开连接
✓ 点击 "Clear" 清空日志
```

**预期结果**:
- ✅ 连接指示器显示绿色
- ✅ 事件日志实时更新
- ✅ 不同事件类型有不同颜色
- ✅ 执行输出逐字符显示
- ✅ 执行完成后停止按钮禁用
- ✅ 错误情况有明确提示

---

## 🔍 完整功能回归测试

### 1. 用户认证流程
```bash
# 访问
http://localhost:3000/auth/login

# 测试
✓ 注册新用户
✓ 登录已有用户
✓ 登出功能
✓ Token 刷新
```

### 2. 工作流管理
```bash
# 访问
http://localhost:3000/workflows

# 测试
✓ 创建新工作流
✓ 编辑工作流
✓ 删除工作流
✓ 复制工作流
✓ 批量删除（选中多个）
✓ 搜索工作流
✓ 按状态筛选
✓ 按标签筛选
```

### 3. 模板市场
```bash
# 访问
http://localhost:3000/marketplace

# 测试
✓ 浏览模板列表
✓ 搜索模板
✓ 按分类筛选
✓ 按标签筛选
✓ 排序（热门/最新/评分）
✓ 分页浏览
✓ 查看模板详情
✓ 使用模板创建工作流
✓ 收藏模板
✓ 取消收藏
```

### 4. 发布和分享
```bash
# 在工作流编辑器中测试

# 测试发布
✓ 点击 "Publish" 按钮
✓ 填写模板信息
✓ 选择分类
✓ 添加标签
✓ 添加图标URL
✓ 提交发布

# 测试分享
✓ 点击 "Share" 按钮
✓ 选择权限（View/Edit/Execute）
✓ 设置过期时间
✓ 设置使用次数限制
✓ 生成分享链接
✓ 复制链接
```

### 5. 用户资料
```bash
# 访问
http://localhost:3000/profile

# 测试
✓ 查看用户信息
✓ 上传头像
✓ 删除头像
✓ 查看统计数据
✓ 查看我的模板
```

---

## 🐛 常见问题排查

### 问题1: 头像上传失败
```bash
# 检查
1. 后端 uploads/avatars 目录存在吗？
2. 文件大小是否超过 5MB？
3. 文件格式是否支持？
4. Token 是否有效？

# 解决
mkdir -p backend/uploads/avatars
chmod 755 backend/uploads/avatars
```

### 问题2: 分页不显示
```bash
# 检查
1. 后端返回的数据格式正确吗？
2. totalCount > 0 吗？
3. 控制台有错误吗？

# 调试
# 打开浏览器控制台，查看网络请求
# 确认响应包含 items, total, page, page_size, total_pages
```

### 问题3: WebSocket 连接失败
```bash
# 检查
1. 后端 WebSocket 端点是否运行？
2. URL 是否正确（ws://localhost:8000）？
3. 防火墙是否阻止？
4. 浏览器控制台有什么错误？

# 测试
# 打开浏览器控制台 Network 标签
# 筛选 WS（WebSocket）
# 查看连接状态和消息
```

### 问题4: 静态文件404
```bash
# 检查
1. FastAPI 是否挂载了 /uploads 路径？
2. 文件是否真实存在？
3. 文件权限是否正确？

# 验证
curl http://localhost:8000/uploads/avatars/test.jpg
ls -la backend/uploads/avatars/
```

---

## 📊 性能测试

### 头像上传性能
```bash
# 测试不同大小的图片
- 100KB 图片: < 1秒
- 1MB 图片: < 2秒
- 5MB 图片: < 5秒
```

### 分页加载性能
```bash
# 测试不同数据量
- 10条/页: < 200ms
- 50条/页: < 500ms
- 100条/页: < 1s
```

### WebSocket 延迟
```bash
# 测试事件延迟
- 连接建立: < 100ms
- 事件传输: < 50ms
- Token 流式输出: 实时
```

---

## ✅ 测试检查清单

### 后端测试 ✓
- [ ] 头像上传端点工作正常
- [ ] 头像删除端点工作正常
- [ ] 静态文件服务正常
- [ ] 分页API返回正确格式
- [ ] WebSocket 连接稳定

### 前端测试 ✓
- [ ] 头像上传组件显示正常
- [ ] 分页组件交互正常
- [ ] WebSocket 测试页面工作
- [ ] 所有页面无控制台错误
- [ ] 响应式设计正常

### 集成测试 ✓
- [ ] 端到端工作流执行
- [ ] 用户完整操作流程
- [ ] 多用户并发测试
- [ ] 错误处理和恢复

### 边界测试 ✓
- [ ] 大文件上传（超过限制）
- [ ] 非法文件类型
- [ ] 空数据分页
- [ ] WebSocket 异常断开

---

## 🎯 测试通过标准

### 功能性
- ✅ 所有功能按预期工作
- ✅ 无明显 bug 或崩溃
- ✅ 错误处理得当

### 性能
- ✅ 页面加载 < 2秒
- ✅ API 响应 < 1秒
- ✅ WebSocket 延迟 < 100ms

### 用户体验
- ✅ 界面友好直观
- ✅ 反馈及时清晰
- ✅ 错误提示明确

### 代码质量
- ✅ TypeScript 无错误
- ✅ 控制台无警告
- ✅ 网络请求合理

---

## 📝 测试报告模板

```markdown
# 测试报告

**测试人**: ___________
**测试日期**: ___________
**版本**: v2.3.0

## 测试结果

### Task 22: 头像上传
- [ ] 上传功能: ✅ / ❌
- [ ] 删除功能: ✅ / ❌
- [ ] 文件验证: ✅ / ❌
- **问题**: ___________

### Task 25: 分页组件
- [ ] 页码切换: ✅ / ❌
- [ ] 每页大小: ✅ / ❌
- [ ] 快速跳转: ✅ / ❌
- **问题**: ___________

### Task 23: WebSocket 测试
- [ ] 连接建立: ✅ / ❌
- [ ] 事件接收: ✅ / ❌
- [ ] 执行完成: ✅ / ❌
- **问题**: ___________

## 总体评价
- **通过**: ✅ / ❌
- **备注**: ___________
```

---

**祝测试顺利！** 🎉

如有问题，请参考：
- 完成报告: `PHASE3_COMPLETION_REPORT.md`
- 项目文档: `DOCUMENTATION_INDEX.md`
- API 文档: `http://localhost:8000/docs`
