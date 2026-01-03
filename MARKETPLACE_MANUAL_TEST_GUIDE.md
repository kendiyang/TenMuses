# TenMuses 模板市场 - 手动测试指南

**日期**: 2026年1月3日  
**测试环境**: localhost:3000 (前端) & localhost:8000 (后端)

---

## 🚀 启动服务

### 后端启动
```bash
cd /Users/mg/Workspace/TenMuses/backend
/Users/mg/Workspace/TenMuses/backend/venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
✅ 预期: 服务启动在 http://localhost:8000

### 前端启动  
```bash
cd /Users/mg/Workspace/TenMuses/frontend
npm run dev
```
✅ 预期: 服务启动在 http://localhost:3000

### 数据库和缓存
- PostgreSQL: 运行在 Docker (tenmuses-postgres-dev)
- Redis: 运行在 Docker (tenmuses-redis-1)
- 10 个示例模板已初始化

---

## 📋 测试场景

### 1️⃣ 用户认证 (必须首先执行)

**路径**: http://localhost:3000/auth/login

#### 测试步骤:
1. 打开登录页面
2. 使用以下凭证登录:
   - 邮箱: `testuser@example.com`
   - 密码: `Test123!@#`

**预期结果**:
- ✅ 成功登录
- ✅ 重定向到首页或仪表板
- ✅ 页面显示欢迎信息或用户信息

---

### 2️⃣ 市场首页浏览

**路径**: http://localhost:3000/marketplace

#### 页面加载验证
- ✅ 页面正确渲染，无错误
- ✅ 显示"Template Marketplace"标题
- ✅ 看到两个主要部分:
  - **Top Picks** (顶部精选): 3个精选模板
  - **All Templates** (全部模板): 网格显示所有模板

#### 顶部精选验证
- ✅ 显示3个精选模板卡片
- ✅ 每个卡片包含: 名称, 描述, 类别, "Try it now" 按钮
- ✅ 卡片有渐变背景和悬停效果

#### 全部模板验证
- ✅ 显示所有10个模板
- ✅ 响应式布局 (桌面3列, 平板2列, 手机1列)
- ✅ 每个卡片包含: 标题, 描述, 作者, ⭐评分, 📊使用次数, ❤️收藏按钮

---

### 3️⃣ 搜索功能

**位置**: All Templates 部分的搜索框

#### 测试步骤:
- 搜索 "Blog" → 显示: Blog Post Generator
- 搜索 "Analysis" → 显示: Data Analysis & Insights, Customer Feedback Analysis, Competitive Analysis Report
- 搜索 "Marketing" → 显示: Email Marketing Campaign Generator, Social Media Content Planner

**预期结果**: ✅ 模板列表实时过滤，符合搜索词

---

### 4️⃣ 类别过滤

**位置**: All Templates 的类别按钮行

#### 测试步骤:
- 点击 "Content Creation" → 显示3个
- 点击 "Business" → 显示3个
- 点击 "Marketing" → 显示2个
- 点击 "Featured" → 恢复显示所有10个

**预期结果**: 
- ✅ 按钮高亮变色
- ✅ 列表只显示该类别的模板

---

### 5️⃣ 模板卡片交互

#### 点击卡片导航
- ✅ 点击任何模板卡片 → URL变更为 `/marketplace/templates/[id]`

#### 收藏按钮
- ✅ 首次点击 ❤️ → 心形填充为红色 (已收藏)
- ✅ 第二次点击 → 心形变回空心 (取消收藏)

#### Top Picks "Try it now"
- ✅ 点击按钮 → 创建工作流并重定向到 `/workflows/[id]`

---

### 6️⃣ 模板详情页面

**路径**: http://localhost:3000/marketplace/templates/[id]

#### 页面元素
- ✅ 返回按钮
- ✅ 模板名称、描述、作者
- ✅ 评分、使用次数、收藏数
- ✅ "Use template" 按钮
- ✅ "Save template" / "Saved" 按钮
- ✅ "Share" 按钮
- ✅ 评论部分

#### 交互测试
- ✅ 点击 "Use template" → 创建工作流，重定向到编辑器
- ✅ 点击 "Save template" → 状态切换为 "Saved"
- ✅ 提交评论 → 评论出现在列表中

---

### 7️⃣ API集成验证

#### 获取模板列表
```bash
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/v1/marketplace/templates
```
**预期**: 返回10个模板

#### 收藏模板
```bash
curl -X POST \
  -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/v1/marketplace/templates/[id]/favorite
```
**预期**: HTTP 201 Created

---

## ✅ 完整流程测试

1. 登录 → 2. 浏览市场 → 3. 搜索 → 4. 过滤 → 5. 查看详情 → 6. 收藏 → 7. 使用模板 → 8. 评论 → 9. 返回

---

## 📊 测试检查清单

- [ ] 后端服务运行在 :8000
- [ ] 前端服务运行在 :3000
- [ ] 可以成功登录
- [ ] 市场首页加载正确
- [ ] Top Picks 显示3个模板
- [ ] All Templates 显示10个模板
- [ ] 搜索功能工作
- [ ] 类别过滤工作
- [ ] 可以点击进入模板详情
- [ ] 可以收藏/取消收藏模板
- [ ] 可以使用模板创建工作流
- [ ] 可以添加评论
- [ ] API返回正确的数据
- [ ] 没有控制台错误
- [ ] 响应式设计工作

---

**状态**: ✅ 所有服务运行正常，可开始人工测试
