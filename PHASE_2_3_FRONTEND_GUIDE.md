# Phase 2.3 RAG - 前端集成实现指南

## 📋 任务 3-5: 前端知识库 UI 集成

本文档详细说明如何在 TenMuses 前端中实现知识库管理和搜索功能。

---

## 任务 3: 知识库管理页面

### 3.1 页面结构

创建文件: `frontend/src/app/knowledge-base/page.tsx`

```typescript
// 主页面布局
export default function KnowledgeBasePage() {
  return (
    <div className="flex h-full gap-4 p-6">
      {/* 左侧：文档列表 */}
      <DocumentsList />
      
      {/* 中间：操作区域 */}
      <div className="flex-1 flex flex-col gap-4">
        <UploadSection />
        <SearchSection />
      </div>
      
      {/* 右侧：文档详情 */}
      <DocumentDetail />
    </div>
  )
}
```

### 3.2 关键组件

#### 3.2.1 DocumentsList 组件
文件: `frontend/src/components/knowledge/DocumentsList.tsx`

**功能:**
- 显示用户上传的所有文档
- 分页加载（每页 10 个）
- 点击选中文档
- 显示文档元数据（大小、上传时间、分片数）

**API 调用:**
```
GET /api/v1/kb/documents?page=1&limit=10
```

**渲染项:**
```
[文档列表]
├─ 文档名称
├─ 上传时间
├─ 文件大小
├─ 分片数
└─ 删除按钮
```

#### 3.2.2 UploadSection 组件
文件: `frontend/src/components/knowledge/UploadSection.tsx`

**功能:**
- 拖拽上传文件
- 支持的格式：PDF、DOCX、TXT、Markdown
- 显示上传进度
- 处理上传错误

**API 调用:**
```
POST /api/v1/kb/documents
Content-Type: multipart/form-data
  - file: File
  - metadata?: JSON
```

**实现步骤:**
1. 拖拽检测和 FileInput
2. 文件验证（格式、大小）
3. FormData 构建
4. 上传进度跟踪
5. 错误处理和重试

#### 3.2.3 DocumentDetail 组件
文件: `frontend/src/components/knowledge/DocumentDetail.tsx`

**功能:**
- 显示选中文档的详细信息
- 显示分片列表
- 显示内容预览
- 删除文档确认对话框

**显示内容:**
```
文档详情
├─ 标题和元数据
├─ 文件大小、格式
├─ 上传时间、处理时间
├─ 分片数量
└─ 分片列表（可折叠）
  ├─ 分片 1: [内容预览...]
  ├─ 分片 2: [内容预览...]
  └─ ...
```

### 3.3 删除确认对话框
文件: `frontend/src/components/knowledge/DeleteConfirmDialog.tsx`

```typescript
interface DeleteConfirmDialogProps {
  isOpen: boolean
  documentName: string
  onConfirm: () => Promise<void>
  onCancel: () => void
}
```

**API 调用:**
```
DELETE /api/v1/kb/documents/{document_id}
```

---

## 任务 4: 搜索和结果展示

### 4.1 SearchSection 组件
文件: `frontend/src/components/knowledge/SearchSection.tsx`

**功能:**
- 搜索输入框
- 搜索模式切换（文档级 / 分片级）
- 相关性阈值滑块
- 执行搜索

**API 调用:**
```
POST /api/v1/kb/search
{
  "query": "搜索关键词",
  "top_k": 10,
  "min_score": 0.5,
  "search_chunks": false  // false = 文档级, true = 分片级
}
```

### 4.2 SearchResults 组件
文件: `frontend/src/components/knowledge/SearchResults.tsx`

**显示结构:**
```
搜索结果 (找到 3 个相关文档)
├─ 结果 1
│  ├─ 标题: [文档名称]
│  ├─ 相关性: [得分 95%]
│  ├─ 摘要: [内容预览...]
│  ├─ 分片数: [该文档匹配的分片数]
│  └─ [查看详情] [在图中使用]
│
├─ 结果 2
│  └─ ...
│
└─ 结果 3
   └─ ...
```

### 4.3 搜索模式切换
```typescript
enum SearchMode {
  DOCUMENT = "document",  // 文档级搜索，返回整个文档
  CHUNK = "chunk"         // 分片级搜索，返回匹配的分片
}
```

**用户选择的 UI:**
```
[ ● 文档级搜索 | ○ 分片级搜索 ]
```

---

## 任务 5: 工作流节点中的 RAG 集成

### 5.1 RAG 节点配置面板
文件: `frontend/src/components/canvas/RagNodeConfig.tsx`

**在 SmartNode 中添加 RAG 配置选项:**

```typescript
interface RagNodeConfig {
  enableRag: boolean           // 启用/禁用 RAG
  knowledge_documents?: UUID[] // 选择知识库文档
  topK?: number               // 返回最相关的 K 个结果
  minScore?: number           // 最低相关性阈值
  ragMode?: 'document' | 'chunk'  // 搜索模式
}
```

### 5.2 节点属性面板中的 RAG 选项
文件: `frontend/src/components/canvas/NodePropertyPanel.tsx`

**在现有属性面板中添加:**

```
[高级选项]
├─ [ ] 启用 RAG 检索
│  ├─ 选择知识库: [下拉菜单]
│  │  └─ [选择文档...]
│  ├─ Top K: [数字输入] (默认: 5)
│  ├─ 最低分数: [滑块] (0.0 - 1.0)
│  └─ 搜索模式:
│     ├─ ○ 文档级（返回整个文档）
│     └─ ○ 分片级（返回匹配段落）
│
└─ 上下文预览:
   └─ [如果启用 RAG，显示格式化的上下文预览]
```

### 5.3 上下文预览面板
文件: `frontend/src/components/knowledge/ContextPreview.tsx`

**显示内容:**
```
RAG 上下文预览 (预计 150 tokens)

1. 来自"AI 工作流编排指南" - 相关性: 0.92
   工作流是由多个节点组成的有向图...
   
2. 来自"知识库检索最佳实践" - 相关性: 0.87
   在检索时应该选择合适的分片大小...
   
3. 来自"多智能体协作模式" - 相关性: 0.81
   使用 LangGraph 可以实现...
```

**功能:**
- 实时获取上下文预览
- 显示 token 计数
- 显示相关性评分
- 点击可编辑 RAG 参数

### 5.4 后端集成

在工作流执行时，后端在 LLM 节点执行前获取 RAG 上下文：

```python
# 后端逻辑
if node_config.enableRag:
    context = await rag_service.search_chunks(
        query=user_query,
        user_id=user_id,
        top_k=node_config.topK
    )
    formatted_context = rag_service.format_context(context)
    
    # 注入到 LLM prompt 中
    enhanced_prompt = f"""
    {original_prompt}
    
    ---
    相关背景信息:
    {formatted_context}
    """
    
    response = await llm_client.invoke(enhanced_prompt, ...)
```

---

## 实现步骤总结

### Week 2 Day 5-6: 知识库管理 UI
1. ✅ 创建 `/knowledge-base` 页面和布局
2. ✅ 实现 DocumentsList 组件（分页、选择）
3. ✅ 实现 UploadSection 组件（拖拽、格式验证）
4. ✅ 实现 DocumentDetail 和 DeleteConfirmDialog
5. ✅ 集成所有组件，连接后端 API

### Week 2 Day 7: 搜索功能
1. ✅ 实现 SearchSection 组件
2. ✅ 实现 SearchResults 组件
3. ✅ 添加搜索模式切换
4. ✅ 处理搜索加载和错误状态

### Week 3 Day 1-2: 工作流节点集成
1. ✅ 在 NodePropertyPanel 中添加 RAG 配置选项
2. ✅ 实现 RagNodeConfig 组件
3. ✅ 实现 ContextPreview 组件
4. ✅ 连接到工作流执行时的后端调用

---

## 技术细节

### 状态管理
使用 Zustand（现有 store）：

```typescript
// 添加到 useWorkflowStore
const workflowStore = create<WorkflowStore>((set) => ({
  knowledgeBase: {
    documents: [],
    selectedDocId: null,
    isLoading: false,
    error: null
  },
  searchResults: [],
  setKnowledgeDocuments: (docs) => set(state => ({
    knowledgeBase: { ...state.knowledgeBase, documents: docs }
  })),
  // ... 其他 actions
}))
```

### 错误处理
```typescript
try {
  const response = await fetch('/api/v1/kb/documents', {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` },
    body: formData
  })
  
  if (!response.ok) {
    throw new Error(`上传失败: ${response.status}`)
  }
  
  const data = await response.json()
  // 处理成功
} catch (error) {
  // 显示用户友好的错误信息
  toast.error(`上传失败: ${error.message}`)
}
```

### 性能优化
1. 文档列表虚拟化（使用 react-window）
2. 搜索结果缓存（使用 React Query）
3. 图片预加载（PDF 预览）
4. 分片内容懒加载

### 无障碍 (A11y)
- 为所有按钮添加 aria-label
- 键盘导航支持（Tab、Enter）
- 搜索结果的屏幕阅读器支持
- 适当的颜色对比度

---

## 测试清单

### 单元测试
- [ ] DocumentsList 分页逻辑
- [ ] UploadSection 文件验证
- [ ] SearchResults 结果排序

### 集成测试
- [ ] 完整的上传 → 列表 → 删除 流程
- [ ] 搜索 → 结果显示 → 上下文预览 流程
- [ ] 在工作流中使用 RAG 节点

### E2E 测试
- [ ] 用户完整的知识库使用场景

---

## 下一步

完成前端后，推荐的改进方向：

1. **后端任务队列** (Task 6)
   - 使用 Celery + Redis 异步处理大文件
   - 向量化进度跟踪

2. **缓存优化** (Task 7)
   - Redis 缓存热门查询
   - 向量搜索结果缓存

3. **单元测试** (Task 8)
   - RAG 组件测试
   - API 集成测试

