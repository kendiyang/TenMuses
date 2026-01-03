# Phase 2.5 RAG Frontend Implementation Guide

## 概述

Frontend RAG 实现包括：
1. **知识库管理页面** - 主页面（已有框架）
2. **文档上传组件** - UploadSection（需完成）
3. **文档列表组件** - DocumentsList（需完成）
4. **搜索组件** - SearchSection（需完成）
5. **RAG 节点配置** - RagNodeConfig.tsx（需增强）
6. **WebSocket 集成** - 事件流处理（需完成）

---

## 📁 文件结构

```
frontend/src/
├── app/
│   └── knowledge-base/
│       └── page.tsx          # 主页面（框架存在）
├── components/
│   ├── knowledge/            # 新建目录
│   │   ├── UploadSection.tsx         # 文档上传
│   │   ├── DocumentsList.tsx         # 文档列表
│   │   ├── SearchSection.tsx         # 搜索界面
│   │   ├── DocumentDetail.tsx        # 文档详情
│   │   ├── SearchResults.tsx         # 搜索结果展示
│   │   └── DocumentSelector.tsx      # 下拉选择器（RAG 节点用）
│   └── canvas/
│       └── RagNodeConfig.tsx  # RAG 节点配置（需增强）
└── hooks/
    └── useKnowledgeBase.ts   # 自定义 hook（可选）
```

---

## 🎯 Task 6: Frontend Knowledge Management Page (8h)

### 6.1 UploadSection Component

**File**: `frontend/src/components/knowledge/UploadSection.tsx`

```typescript
/**
 * Document Upload Component
 * 支持拖拽上传、多文件上传
 */

'use client'

import React, { useState, useRef } from 'react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { AlertCircle, Upload, File } from 'lucide-react'

interface UploadSectionProps {
  onUploadSuccess?: (document: any) => void
  onError?: (error: string) => void
}

const SUPPORTED_TYPES = [
  'application/pdf',
  'text/plain',
  'text/markdown',
  'text/html',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'application/vnd.openxmlformats-officedocument.presentationml.presentation',
]

const MIME_TYPE_NAMES = {
  'application/pdf': 'PDF',
  'text/plain': 'Text',
  'text/markdown': 'Markdown',
  'text/html': 'HTML',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'Word',
  'application/vnd.openxmlformats-officedocument.presentationml.presentation': 'PowerPoint',
}

export default function UploadSection({
  onUploadSuccess,
  onError,
}: UploadSectionProps) {
  const [isDragging, setIsDragging] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [uploadProgress, setUploadProgress] = useState<Map<string, number>>(new Map())
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleDragEnter = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(true)
  }

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)
  }

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)

    const files = Array.from(e.dataTransfer.files)
    await uploadFiles(files)
  }

  const uploadFiles = async (files: File[]) => {
    setError(null)
    setIsUploading(true)

    try {
      for (const file of files) {
        // 验证文件类型
        if (!SUPPORTED_TYPES.includes(file.type)) {
          throw new Error(`不支持的文件类型: ${file.type}`)
        }

        // 验证文件大小（最大 50MB）
        if (file.size > 50 * 1024 * 1024) {
          throw new Error(`文件过大: ${file.name}（最大 50MB）`)
        }

        // 上传文件
        const formData = new FormData()
        formData.append('file', file)

        const response = await fetch('/api/v1/kb/upload', {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${localStorage.getItem('accessToken')}`,
          },
          body: formData,
        })

        if (!response.ok) {
          throw new Error(`上传失败: ${response.statusText}`)
        }

        const data = await response.json()
        onUploadSuccess?.(data.data)

        // 清除进度
        const newProgress = new Map(uploadProgress)
        newProgress.delete(file.name)
        setUploadProgress(newProgress)
      }
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : '上传失败'
      setError(errorMsg)
      onError?.(errorMsg)
    } finally {
      setIsUploading(false)
    }
  }

  return (
    <Card className="p-6 border-2 border-dashed hover:border-primary/50 transition-colors">
      <div
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`text-center py-8 cursor-pointer transition-all ${
          isDragging ? 'bg-primary/10 border-primary rounded-lg' : ''
        }`}
      >
        <Upload className="mx-auto h-12 w-12 text-gray-400 mb-4" />
        <h3 className="text-lg font-semibold mb-2">上传文档</h3>
        <p className="text-gray-600 mb-4">
          拖拽文件到这里或{' '}
          <button
            onClick={() => fileInputRef.current?.click()}
            className="text-primary hover:underline"
          >
            点击选择
          </button>
        </p>

        <div className="text-sm text-gray-500 mb-4">
          <p className="font-semibold mb-2">支持格式:</p>
          <div className="flex flex-wrap gap-2 justify-center">
            {Object.values(MIME_TYPE_NAMES).map((name) => (
              <span key={name} className="bg-gray-100 px-2 py-1 rounded text-xs">
                {name}
              </span>
            ))}
          </div>
          <p className="text-xs mt-2">最大文件大小: 50MB</p>
        </div>

        <input
          ref={fileInputRef}
          type="file"
          multiple
          hidden
          onChange={(e) => {
            const files = Array.from(e.currentTarget.files || [])
            uploadFiles(files)
          }}
          accept={SUPPORTED_TYPES.join(',')}
        />
      </div>

      {error && (
        <div className="mt-4 p-3 bg-red-100 border border-red-300 text-red-700 rounded-lg flex gap-2">
          <AlertCircle className="h-5 w-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {isUploading && (
        <div className="mt-4 space-y-2">
          <p className="text-sm font-semibold">上传中...</p>
          <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
            <div className="h-full bg-primary animate-pulse w-1/3" />
          </div>
        </div>
      )}
    </Card>
  )
}
```

### 6.2 DocumentsList Component

**File**: `frontend/src/components/knowledge/DocumentsList.tsx`

```typescript
/**
 * Documents List Component
 * 展示、编辑、删除文档
 */

'use client'

import React, { useState } from 'react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { File, Trash2, Eye, Clock } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import { zhCN } from 'date-fns/locale'

interface Document {
  id: string
  title: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  chunk_count: number
  created_at: string
  doc_metadata?: Record<string, any>
}

interface DocumentsListProps {
  documents: Document[]
  isLoading?: boolean
  onDelete?: (id: string) => Promise<void>
  onSelect?: (doc: Document) => void
}

export default function DocumentsList({
  documents,
  isLoading,
  onDelete,
  onSelect,
}: DocumentsListProps) {
  const [deleting, setDeleting] = useState<string | null>(null)

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      pending: 'bg-yellow-100 text-yellow-800',
      processing: 'bg-blue-100 text-blue-800',
      completed: 'bg-green-100 text-green-800',
      failed: 'bg-red-100 text-red-800',
    }
    return colors[status] || 'bg-gray-100 text-gray-800'
  }

  const getStatusLabel = (status: string) => {
    const labels: Record<string, string> = {
      pending: '待处理',
      processing: '处理中',
      completed: '已完成',
      failed: '失败',
    }
    return labels[status] || status
  }

  if (isLoading) {
    return (
      <Card className="p-6">
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-20 bg-gray-100 rounded animate-pulse" />
          ))}
        </div>
      </Card>
    )
  }

  if (documents.length === 0) {
    return (
      <Card className="p-6 text-center py-12">
        <File className="mx-auto h-12 w-12 text-gray-400 mb-2" />
        <p className="text-gray-600">还没有文档，请先上传</p>
      </Card>
    )
  }

  return (
    <div className="space-y-3">
      {documents.map((doc) => (
        <Card key={doc.id} className="p-4">
          <div className="flex items-start justify-between">
            <div className="flex-1 cursor-pointer" onClick={() => onSelect?.(doc)}>
              <div className="flex items-center gap-3 mb-2">
                <File className="h-5 w-5 text-primary" />
                <h4 className="font-semibold hover:text-primary transition-colors">
                  {doc.title}
                </h4>
                <span className={`text-xs px-2 py-1 rounded-full ${getStatusColor(doc.status)}`}>
                  {getStatusLabel(doc.status)}
                </span>
              </div>

              <div className="flex items-center gap-4 text-sm text-gray-600">
                <span>📦 {doc.chunk_count} 个分片</span>
                <span className="flex items-center gap-1">
                  <Clock className="h-4 w-4" />
                  {formatDistanceToNow(new Date(doc.created_at), { locale: zhCN })}前
                </span>
              </div>
            </div>

            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => onSelect?.(doc)}
                title="查看详情"
              >
                <Eye className="h-4 w-4" />
              </Button>

              <Button
                variant="destructive"
                size="sm"
                onClick={async () => {
                  setDeleting(doc.id)
                  try {
                    await onDelete?.(doc.id)
                  } finally {
                    setDeleting(null)
                  }
                }}
                disabled={deleting === doc.id}
                title="删除文档"
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </Card>
      ))}
    </div>
  )
}
```

### 6.3 SearchSection Component

**File**: `frontend/src/components/knowledge/SearchSection.tsx`

```typescript
/**
 * Knowledge Base Search Component
 * 实时搜索、结果展示、过滤选项
 */

'use client'

import React, { useState, useCallback } from 'react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Search, Loader2 } from 'lucide-react'
import SearchResults from './SearchResults'

interface SearchSectionProps {
  documentIds?: string[]
  onSearch?: (query: string, results: any[]) => void
}

export default function SearchSection({
  documentIds,
  onSearch,
}: SearchSectionProps) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [isSearching, setIsSearching] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [topK, setTopK] = useState(10)
  const [minScore, setMinScore] = useState(0.7)

  const handleSearch = useCallback(async () => {
    if (!query.trim()) return

    setIsSearching(true)
    setError(null)

    try {
      const params = new URLSearchParams({
        query,
        top_k: topK.toString(),
        min_score: minScore.toString(),
      })

      if (documentIds?.length) {
        params.append('document_ids', documentIds.join(','))
      }

      const response = await fetch(`/api/v1/kb/search?${params}`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('accessToken')}`,
        },
      })

      if (!response.ok) throw new Error('搜索失败')

      const data = await response.json()
      setResults(data.data?.results || [])
      onSearch?.(query, data.data?.results || [])
    } catch (err) {
      setError(err instanceof Error ? err.message : '搜索失败')
    } finally {
      setIsSearching(false)
    }
  }, [query, topK, minScore, documentIds, onSearch])

  return (
    <div className="space-y-4">
      <Card className="p-4">
        <div className="space-y-3">
          <div className="flex gap-2">
            <input
              type="text"
              placeholder="输入搜索关键词..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              className="flex-1 px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
            />
            <Button
              onClick={handleSearch}
              disabled={isSearching || !query.trim()}
              className="gap-2"
            >
              {isSearching && <Loader2 className="h-4 w-4 animate-spin" />}
              {isSearching ? '搜索中' : '搜索'}
            </Button>
          </div>

          <div className="flex gap-4 text-sm">
            <label className="flex items-center gap-2">
              <span>返回数量:</span>
              <input
                type="number"
                min="1"
                max="20"
                value={topK}
                onChange={(e) => setTopK(parseInt(e.target.value))}
                className="w-16 px-2 py-1 border rounded"
              />
            </label>

            <label className="flex items-center gap-2">
              <span>最小相关度:</span>
              <input
                type="number"
                min="0"
                max="1"
                step="0.1"
                value={minScore}
                onChange={(e) => setMinScore(parseFloat(e.target.value))}
                className="w-16 px-2 py-1 border rounded"
              />
            </label>
          </div>

          {error && (
            <div className="text-red-600 text-sm">❌ {error}</div>
          )}
        </div>
      </Card>

      {results.length > 0 && (
        <SearchResults results={results} query={query} />
      )}
    </div>
  )
}
```

---

## 🎯 Task 7: RAG Node Configuration Component (6h)

**File**: `frontend/src/components/canvas/RagNodeConfig.tsx` (enhance existing)

```typescript
/**
 * RAG Node Configuration Component
 * 在节点配置面板中配置 RAG 参数
 */

'use client'

import React, { useCallback } from 'react'
import { Card } from '@/components/ui/card'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Slider } from '@/components/ui/slider'
import DocumentSelector from '@/components/knowledge/DocumentSelector'
import { useWorkflowStore } from '@/stores/workflow'

interface RagNodeConfigProps {
  nodeId: string
  config?: any
}

export default function RagNodeConfig({
  nodeId,
  config = {},
}: RagNodeConfigProps) {
  const updateNodeConfig = useWorkflowStore((state) => state.updateNodeConfig)

  const handleConfigChange = useCallback(
    (key: string, value: any) => {
      updateNodeConfig(nodeId, {
        ...config,
        [key]: value,
      })
    },
    [nodeId, config, updateNodeConfig]
  )

  return (
    <div className="space-y-4">
      <Card className="p-4">
        <h3 className="font-semibold mb-3">RAG 配置</h3>

        {/* 搜索模式 */}
        <div className="mb-4">
          <label className="text-sm font-medium mb-2 block">搜索模式</label>
          <Select
            value={config.search_mode || 'chunk'}
            onValueChange={(value) => handleConfigChange('search_mode', value)}
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="chunk">分片级搜索（精确）</SelectItem>
              <SelectItem value="document">文档级搜索（快速）</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* 返回数量 */}
        <div className="mb-4">
          <label className="text-sm font-medium mb-2 block">
            返回结果数 ({config.top_k || 10})
          </label>
          <Slider
            min={1}
            max={20}
            step={1}
            value={[config.top_k || 10]}
            onValueChange={(value) => handleConfigChange('top_k', value[0])}
          />
        </div>

        {/* 最小相关度 */}
        <div className="mb-4">
          <label className="text-sm font-medium mb-2 block">
            最小相关度 ({(config.min_score || 0.7).toFixed(2)})
          </label>
          <Slider
            min={0}
            max={1}
            step={0.05}
            value={[config.min_score || 0.7]}
            onValueChange={(value) => handleConfigChange('min_score', value[0])}
          />
        </div>

        {/* 文档选择 */}
        <div className="mb-4">
          <label className="text-sm font-medium mb-2 block">选择文档（可选）</label>
          <DocumentSelector
            selectedIds={config.document_ids || []}
            onSelect={(ids) => handleConfigChange('document_ids', ids)}
          />
        </div>

        {/* 去重选项 */}
        <div className="mb-4">
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={config.deduplicate || false}
              onChange={(e) => handleConfigChange('deduplicate', e.target.checked)}
              className="w-4 h-4 rounded"
            />
            <span className="text-sm">每个文档仅返回最相关的分片</span>
          </label>
        </div>

        {/* 格式化选项 */}
        <div className="mb-4">
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={config.include_metadata !== false}
              onChange={(e) => handleConfigChange('include_metadata', e.target.checked)}
              className="w-4 h-4 rounded"
            />
            <span className="text-sm">在上下文中包含元数据（来源、相关度）</span>
          </label>
        </div>
      </Card>
    </div>
  )
}
```

---

## 🎯 Task 8: WebSocket RAG Event Integration (4h)

**File**: `frontend/src/lib/websocket-client.ts` (enhance existing)

Add RAG event handlers:

```typescript
// Add to existing websocket client

export const RAG_EVENT_TYPES = {
  RAG_SEARCH_STARTED: 'rag_search_started',
  RAG_RESULT: 'rag_result',
  RAG_ERROR: 'rag_error',
  RAG_COMPLETE: 'rag_complete',
}

// Handle RAG events
client.on(RAG_EVENT_TYPES.RAG_SEARCH_STARTED, (payload) => {
  console.log('RAG search started:', payload.query)
  updateUIStatus('searching')
})

client.on(RAG_EVENT_TYPES.RAG_RESULT, (payload) => {
  console.log('RAG results:', payload.results)
  displaySearchResults(payload.results)
  displayContext(payload.context)
})

client.on(RAG_EVENT_TYPES.RAG_COMPLETE, () => {
  console.log('RAG search complete')
  updateUIStatus('complete')
})

client.on(RAG_EVENT_TYPES.RAG_ERROR, (payload) => {
  console.error('RAG error:', payload.error)
  showError(payload.error)
})
```

---

## 📊 Implementation Timeline

### Week 1 (Days 6-7)
- [ ] Day 6 (Done): Backend services + migration scripts
- [ ] Day 7: Database setup + API testing
  - [ ] PostgreSQL + pgvector setup
  - [ ] Run migration script
  - [ ] Test APIs with Postman

### Week 2 (Days 8-10)
- [ ] Day 8-9: Frontend components
  - [ ] UploadSection (2h)
  - [ ] DocumentsList (2h)
  - [ ] SearchSection (2h)
  - [ ] DocumentSelector (2h)
- [ ] Day 10: Integration
  - [ ] Knowledge base page assembly
  - [ ] WebSocket RAG events (2h)
  - [ ] End-to-end testing (2h)

---

## 🔗 API Integration Reference

### Upload Endpoint
```
POST /api/v1/kb/upload
Content-Type: multipart/form-data

Body:
  file: <binary file data>

Response:
{
  "data": {
    "id": "uuid",
    "title": "filename",
    "status": "pending",
    "chunk_count": 5,
    "created_at": "2024-..."
  }
}
```

### Search Endpoint
```
POST /api/v1/kb/search
Authorization: Bearer <token>
Content-Type: application/json

Body:
{
  "query": "search terms",
  "top_k": 10,
  "min_score": 0.7,
  "document_ids": ["uuid1", "uuid2"],
  "search_chunks": true
}

Response:
{
  "data": {
    "results": [
      {
        "document_id": "uuid",
        "chunk_id": "uuid",
        "content": "...",
        "score": 0.95,
        "metadata": {...}
      }
    ],
    "total": 3,
    "query": "search terms"
  }
}
```

### List Documents
```
GET /api/v1/kb/documents?skip=0&limit=10&status=completed
Authorization: Bearer <token>

Response:
{
  "data": [
    {
      "id": "uuid",
      "title": "...",
      "status": "completed",
      "chunk_count": 5,
      "created_at": "2024-..."
    }
  ]
}
```

---

## ✅ Verification Checklist

After each component:
- [ ] Component renders without errors
- [ ] All props properly typed
- [ ] Loading and error states handled
- [ ] Accessibility (ARIA labels, keyboard navigation)
- [ ] Responsive design (mobile, tablet, desktop)
- [ ] API error handling
- [ ] User feedback (toast notifications)

---

## 🚀 Performance Optimization Tips

1. **Document List**: Use virtualization for large lists (react-window)
2. **Search Results**: Debounce search input (300ms)
3. **Images**: Lazy load document preview images
4. **Caching**: Cache documents in Zustand store
5. **Pagination**: Implement lazy loading for document lists

---

## 📝 Notes

- All components use Tailwind CSS for styling
- Lucide icons for UI elements
- Date formatting with date-fns
- Accessibility-first approach
- Mobile-responsive design
- Error boundary for graceful degradation

---

**Status**: Ready to start implementation  
**Priority**: High (RAG is P0 feature)  
**Estimated Total Time**: 18 hours  
**Completion Target**: DAY 10
