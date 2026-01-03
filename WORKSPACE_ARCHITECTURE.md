# Workspace 功能规划

## 一、核心功能模块

### 1. Workspace 主页
**功能定位**：用户登录后的中心枢纽，提供快速访问和操作入口

#### 前端功能
- **New 区域**
  - 创建新工作流
  - 5分钟快速教程入口
  - 从模板创建
  
- **Recent Workflows 区域**
  - 显示最近编辑的工作流（最多10个）
  - 显示最后编辑时间
  - 快速打开工作流
  - 显示工作流状态（草稿/已发布/运行中）
  
- **Marketplace 区域**
  - 推荐模板展示
  - 分类筛选（Featured/Content Creation/Business/Chinese等）
  - 模板预览卡片
  - 显示作者、运行次数、评分

#### 后端 API
```python
# 获取用户 workspace 概览
GET /api/v1/workspace
Response: {
  "recent_workflows": [...],  # 最近的工作流
  "statistics": {
    "total_workflows": 10,
    "total_runs": 150,
    "total_templates": 5
  },
  "featured_templates": [...]  # 推荐模板
}

# 获取最近工作流
GET /api/v1/workspace/recent?limit=10
Response: {
  "workflows": [
    {
      "id": "uuid",
      "title": "string",
      "description": "string",
      "updated_at": "datetime",
      "status": "draft|published|running",
      "nodes_count": 5,
      "last_run_at": "datetime"
    }
  ]
}
```

---

## 二、工作流管理

### 2. My Workflows 页面
**功能定位**：管理用户所有工作流

#### 前端功能
- **工作流列表**
  - 网格/列表视图切换
  - 搜索工作流（按名称、描述）
  - 筛选（状态、标签、创建时间）
  - 排序（最近编辑、创建时间、名称）
  
- **工作流操作**
  - 创建新工作流
  - 编辑工作流
  - 复制工作流
  - 删除工作流
  - 导出工作流（JSON）
  - 分享工作流（生成链接）
  - 发布到 Marketplace
  
- **批量操作**
  - 多选工作流
  - 批量删除
  - 批量添加标签
  - 批量导出

#### 后端 API
```python
# 获取工作流列表（带分页和筛选）
GET /api/v1/workflows?page=1&limit=20&search=&status=&sort_by=updated_at&order=desc
Response: {
  "total": 50,
  "page": 1,
  "limit": 20,
  "workflows": [...]
}

# 创建工作流
POST /api/v1/workflows
Body: {
  "title": "string",
  "description": "string",
  "tags": ["tag1", "tag2"],
  "is_public": false
}

# 更新工作流
PUT /api/v1/workflows/{id}
Body: {
  "title": "string",
  "description": "string",
  "canvas_json": {...}
}

# 复制工作流
POST /api/v1/workflows/{id}/duplicate
Response: { "id": "new_workflow_id" }

# 删除工作流
DELETE /api/v1/workflows/{id}

# 批量删除
POST /api/v1/workflows/batch-delete
Body: { "workflow_ids": ["id1", "id2"] }

# 导出工作流
GET /api/v1/workflows/{id}/export
Response: { "workflow": {...} }  # JSON格式

# 分享工作流
POST /api/v1/workflows/{id}/share
Response: {
  "share_link": "https://app.com/shared/{token}",
  "expires_at": "datetime"
}

# 发布到 Marketplace
POST /api/v1/workflows/{id}/publish
Body: {
  "category": "string",
  "tags": ["tag1", "tag2"],
  "thumbnail_url": "string"
}
```

---

## 三、模板管理

### 3. My Templates 页面
**功能定位**：管理用户创建的模板

#### 前端功能
- **模板库**
  - 显示用户发布的模板
  - 显示使用次数、评分
  - 显示收入统计（如果有付费功能）
  
- **模板操作**
  - 编辑模板信息
  - 更新模板版本
  - 设置价格（免费/付费）
  - 取消发布
  - 查看使用统计
  
- **模板分析**
  - 使用趋势图表
  - 用户反馈
  - 收入统计

#### 后端 API
```python
# 获取用户模板
GET /api/v1/templates/my?page=1&limit=20
Response: {
  "total": 5,
  "templates": [
    {
      "id": "uuid",
      "title": "string",
      "description": "string",
      "category": "string",
      "tags": ["tag1"],
      "thumbnail_url": "string",
      "usage_count": 150,
      "rating": 4.5,
      "is_published": true,
      "price": 0,
      "created_at": "datetime"
    }
  ]
}

# 更新模板
PUT /api/v1/templates/{id}
Body: {
  "title": "string",
  "description": "string",
  "category": "string",
  "tags": ["tag1"],
  "price": 0
}

# 取消发布模板
POST /api/v1/templates/{id}/unpublish

# 获取模板统计
GET /api/v1/templates/{id}/statistics
Response: {
  "total_usage": 150,
  "daily_usage": [{"date": "2026-01-01", "count": 10}],
  "user_feedback": [...],
  "revenue": 1000
}
```

---

## 四、Marketplace

### 4. Marketplace 页面
**功能定位**：浏览和使用社区模板

#### 前端功能
- **模板浏览**
  - 分类导航
  - 搜索模板
  - 筛选（价格、评分、使用次数）
  - 排序（热门、最新、评分）
  
- **模板详情**
  - 详细描述
  - 作者信息
  - 使用示例
  - 用户评价
  - 使用统计
  
- **模板使用**
  - 预览模板
  - 使用模板创建工作流
  - 收藏模板
  - 评分和评论
  
- **购买功能**（如果有付费）
  - 购买模板
  - 查看购买历史

#### 后端 API
```python
# 获取 Marketplace 模板
GET /api/v1/marketplace/templates?category=&search=&page=1&limit=20&sort=popular
Response: {
  "total": 100,
  "categories": ["Featured", "Content Creation", "Business"],
  "templates": [...]
}

# 获取模板详情
GET /api/v1/marketplace/templates/{id}
Response: {
  "id": "uuid",
  "title": "string",
  "description": "string",
  "author": {
    "id": "uuid",
    "username": "string",
    "avatar_url": "string"
  },
  "category": "string",
  "tags": ["tag1"],
  "thumbnail_url": "string",
  "usage_count": 150,
  "rating": 4.5,
  "reviews_count": 20,
  "price": 0,
  "workflow_json": {...},
  "created_at": "datetime"
}

# 从模板创建工作流
POST /api/v1/marketplace/templates/{id}/use
Response: {
  "workflow_id": "uuid"
}

# 收藏模板
POST /api/v1/marketplace/templates/{id}/favorite

# 取消收藏
DELETE /api/v1/marketplace/templates/{id}/favorite

# 评价模板
POST /api/v1/marketplace/templates/{id}/reviews
Body: {
  "rating": 5,
  "comment": "string"
}

# 获取模板评价
GET /api/v1/marketplace/templates/{id}/reviews?page=1&limit=10
```

---

## 五、用户设置

### 5. 用户 Profile 页面
**功能定位**：管理个人信息和偏好设置

#### 前端功能
- **个人信息**
  - 头像上传
  - 用户名、邮箱
  - 个人简介
  
- **安全设置**
  - 修改密码
  - API Keys 管理
  - 两步验证
  
- **偏好设置**
  - 语言设置
  - 主题设置
  - 通知偏好
  
- **账户统计**
  - 工作流数量
  - 模板使用次数
  - 账户余额（如果有付费功能）

#### 后端 API
```python
# 获取用户信息
GET /api/v1/users/me
Response: {
  "id": "uuid",
  "email": "string",
  "username": "string",
  "avatar_url": "string",
  "bio": "string",
  "created_at": "datetime",
  "statistics": {
    "workflows_count": 10,
    "templates_count": 2,
    "total_runs": 150
  }
}

# 更新用户信息
PUT /api/v1/users/me
Body: {
  "username": "string",
  "bio": "string"
}

# 上传头像
POST /api/v1/users/me/avatar
Body: FormData with image file

# 修改密码
POST /api/v1/users/me/change-password
Body: {
  "current_password": "string",
  "new_password": "string"
}

# API Keys 管理
GET /api/v1/users/me/api-keys
POST /api/v1/users/me/api-keys
DELETE /api/v1/users/me/api-keys/{id}
```

---

## 六、数据模型扩展

### 需要新增/扩展的数据库表

```python
# 模板表
class Template(Base):
    __tablename__ = "templates"
    
    id = Column(UUID, primary_key=True)
    workflow_id = Column(UUID, ForeignKey('workflows.id'))  # 关联的工作流
    author_id = Column(UUID, ForeignKey('users.id'))
    title = Column(String)
    description = Column(Text)
    category = Column(String)
    tags = Column(ARRAY(String))
    thumbnail_url = Column(String)
    usage_count = Column(Integer, default=0)
    rating = Column(Float, default=0)
    reviews_count = Column(Integer, default=0)
    price = Column(Float, default=0)  # 0表示免费
    is_published = Column(Boolean, default=False)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

# 模板评价表
class TemplateReview(Base):
    __tablename__ = "template_reviews"
    
    id = Column(UUID, primary_key=True)
    template_id = Column(UUID, ForeignKey('templates.id'))
    user_id = Column(UUID, ForeignKey('users.id'))
    rating = Column(Integer)  # 1-5
    comment = Column(Text)
    created_at = Column(DateTime)

# 收藏表
class Favorite(Base):
    __tablename__ = "favorites"
    
    id = Column(UUID, primary_key=True)
    user_id = Column(UUID, ForeignKey('users.id'))
    template_id = Column(UUID, ForeignKey('templates.id'))
    created_at = Column(DateTime)

# 工作流分享表
class WorkflowShare(Base):
    __tablename__ = "workflow_shares"
    
    id = Column(UUID, primary_key=True)
    workflow_id = Column(UUID, ForeignKey('workflows.id'))
    token = Column(String, unique=True)  # 分享令牌
    expires_at = Column(DateTime)
    created_at = Column(DateTime)

# 工作流标签表
class WorkflowTag(Base):
    __tablename__ = "workflow_tags"
    
    id = Column(UUID, primary_key=True)
    workflow_id = Column(UUID, ForeignKey('workflows.id'))
    tag = Column(String)

# 用户统计表（缓存）
class UserStatistics(Base):
    __tablename__ = "user_statistics"
    
    user_id = Column(UUID, ForeignKey('users.id'), primary_key=True)
    workflows_count = Column(Integer, default=0)
    templates_count = Column(Integer, default=0)
    total_runs = Column(Integer, default=0)
    total_favorites = Column(Integer, default=0)
    updated_at = Column(DateTime)
```

---

## 七、前端状态管理

### Zustand Store 扩展

```typescript
// workspace-store.ts
interface WorkspaceStore {
  recentWorkflows: Workflow[]
  statistics: {
    totalWorkflows: number
    totalRuns: number
    totalTemplates: number
  }
  loadRecentWorkflows: () => Promise<void>
  loadStatistics: () => Promise<void>
}

// template-store.ts
interface TemplateStore {
  templates: Template[]
  favorites: string[]
  loadTemplates: () => Promise<void>
  toggleFavorite: (templateId: string) => Promise<void>
}

// marketplace-store.ts
interface MarketplaceStore {
  templates: Template[]
  categories: string[]
  activeCategory: string
  searchQuery: string
  setCategory: (category: string) => void
  setSearchQuery: (query: string) => void
  loadTemplates: () => Promise<void>
}
```

---

## 八、交互流程

### 8.1 用户登录流程
```
1. 用户访问 / → 主页
2. 点击 Sign In → /auth/login
3. 输入邮箱密码 → POST /api/v1/auth/login
4. 登录成功 → 保存 token 到 localStorage
5. 重定向到 /workspace → 显示 Workspace 主页
```

### 8.2 创建工作流流程
```
1. 在 Workspace 点击 "New Workflow"
2. POST /api/v1/workflows → 创建空工作流
3. 返回 workflow_id
4. 重定向到 /workflows/{id} → 打开工作流编辑器
5. 用户编辑工作流 → 自动保存（debounce 2秒）
6. PUT /api/v1/workflows/{id} → 更新工作流
```

### 8.3 使用模板流程
```
1. 在 Marketplace 浏览模板
2. 点击模板卡片 → /marketplace/templates/{id}
3. 查看模板详情
4. 点击 "Use Template"
5. POST /api/v1/marketplace/templates/{id}/use
6. 创建基于模板的工作流
7. 重定向到 /workflows/{new_id}
```

### 8.4 发布模板流程
```
1. 在 My Workflows 选择工作流
2. 点击 "Publish to Marketplace"
3. 填写模板信息（分类、标签、价格）
4. 上传缩略图
5. POST /api/v1/workflows/{id}/publish
6. 创建 Template 记录
7. 重定向到 /templates/my
```

### 8.5 工作流执行流程
```
1. 在工作流编辑器点击 "Run"
2. POST /api/v1/workflows/{id}/run
3. 返回 run_id 和 thread_id
4. 建立 WebSocket 连接 → ws://host/api/v1/ws/run/{thread_id}
5. 发送 {"action": "start", "input": "..."}
6. 接收实时事件：
   - node_started
   - token (流式输出)
   - node_completed
   - run_completed / error
7. 更新 UI 显示执行状态
```

---

## 九、性能优化

### 9.1 前端优化
- 使用 React Query 缓存 API 请求
- 图片懒加载（模板缩略图）
- 虚拟滚动（大量工作流列表）
- 代码分割（按路由拆分）
- Service Worker 缓存静态资源

### 9.2 后端优化
- 数据库查询优化（索引、JOIN优化）
- Redis 缓存热门数据：
  - 用户统计信息
  - 热门模板列表
  - Recent workflows
- 分页和限流
- CDN 加速静态资源（缩略图）
- 异步任务队列（Celery）处理耗时操作

---

## 十、安全考虑

### 10.1 认证授权
- JWT token 过期机制
- 刷新 token 机制
- 权限验证（RBAC）
- API rate limiting

### 10.2 数据安全
- 用户只能访问自己的工作流
- 公开模板需要审核
- 敏感信息加密（API Keys）
- XSS 防护
- CSRF 防护

---

## 十一、监控和日志

### 11.1 前端监控
- Sentry 错误追踪
- Google Analytics 用户行为分析
- 性能监控（Lighthouse）

### 11.2 后端监控
- 日志系统（结构化日志）
- APM 性能监控
- 数据库慢查询监控
- WebSocket 连接监控
- API 调用统计

---

## 十二、实施优先级

### P0 - 核心功能（第一阶段）
1. Workspace 主页基础功能
2. 工作流 CRUD 操作
3. 工作流编辑器集成
4. 工作流执行（WebSocket）
5. 用户认证和基础信息

### P1 - 增强功能（第二阶段）
1. 模板系统基础功能
2. Marketplace 浏览和使用
3. 收藏和评分功能
4. 工作流分享
5. 搜索和筛选

### P2 - 高级功能（第三阶段）
1. 付费模板系统
2. 统计分析功能
3. API Keys 管理
4. 批量操作
5. 导入导出功能

### P3 - 优化功能（第四阶段）
1. 性能优化
2. 缓存机制
3. 监控系统
4. 高级筛选和排序
5. 个性化推荐
