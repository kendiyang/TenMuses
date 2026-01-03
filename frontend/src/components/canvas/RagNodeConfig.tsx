/**
 * RAG Node Configuration Component
 * 路径: frontend/src/components/canvas/RagNodeConfig.tsx
 * 
 * 在工作流节点中集成 RAG 配置
 */

'use client'

import React, { useState, useEffect } from 'react'
import { Card } from '@/components/ui/card'
import { Zap, ChevronDown, ChevronUp, Loader2 } from 'lucide-react'
import { DocumentSelector } from '../knowledge/DocumentSelector'

export interface RagConfig {
  enableRag: boolean
  knowledge_documents?: string[]
  topK?: number
  minScore?: number
  ragMode?: 'document' | 'chunk'
}

interface RagNodeConfigProps {
  value: RagConfig
  onChange: (config: RagConfig) => void
  documents?: Array<{ id: string; filename: string }>
  isLoading?: boolean
}

export default function RagNodeConfig({
  value,
  onChange,
  documents = [],
  isLoading = false,
}: RagNodeConfigProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  const [contextPreview, setContextPreview] = useState('')
  const [loadingContext, setLoadingContext] = useState(false)

  // 加载上下文预览
  const loadContextPreview = async () => {
    if (!value.enableRag || !value.knowledge_documents?.length) {
      setContextPreview('')
      return
    }

    try {
      setLoadingContext(true)
      const response = await fetch('/api/v1/kb/search/context', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('accessToken')}`,
        },
      })

      if (response.ok) {
        const data = await response.json()
        setContextPreview(data.context || '')
      }
    } catch (err) {
      console.error('Load context preview error:', err)
    } finally {
      setLoadingContext(false)
    }
  }

  useEffect(() => {
    if (isExpanded) {
      loadContextPreview()
    }
  }, [isExpanded, value.enableRag, value.knowledge_documents])

  const handleToggleRag = (enabled: boolean) => {
    onChange({
      ...value,
      enableRag: enabled,
    })
  }

  const handleTopKChange = (topK: number) => {
    onChange({
      ...value,
      topK,
    })
  }

  const handleMinScoreChange = (minScore: number) => {
    onChange({
      ...value,
      minScore,
    })
  }

  const handleModeChange = (mode: 'document' | 'chunk') => {
    onChange({
      ...value,
      ragMode: mode,
    })
  }

  return (
    <div className="space-y-3">
      {/* 标题和启用开关 */}
      <div className="flex items-center justify-between p-3 bg-gradient-to-r from-yellow-50 to-amber-50 rounded-lg border border-yellow-200">
        <div className="flex items-center gap-2">
          <Zap className="h-5 w-5 text-yellow-600" />
          <h3 className="font-semibold text-gray-900">RAG 检索配置</h3>
        </div>
        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            checked={value.enableRag}
            onChange={(e) => handleToggleRag(e.target.checked)}
            className="w-4 h-4 rounded"
          />
          <span className="text-sm text-gray-700">
            {value.enableRag ? '启用' : '禁用'}
          </span>
        </label>
      </div>

      {/* 展开/折叠 */}
      {value.enableRag && (
        <div className="border rounded-lg overflow-hidden">
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="w-full flex items-center justify-between p-3 bg-gray-50 hover:bg-gray-100 transition-colors"
          >
            <span className="font-medium text-gray-700">配置选项</span>
            {isExpanded ? (
              <ChevronUp className="h-4 w-4 text-gray-400" />
            ) : (
              <ChevronDown className="h-4 w-4 text-gray-400" />
            )}
          </button>

          {isExpanded && (
            <div className="p-4 space-y-4 bg-white border-t">
              {/* 选择知识库文档 - 使用 DocumentSelector 组件 */}
              <div>
                <label className="block text-sm font-medium text-gray-900 mb-2">
                  选择知识库文档
                </label>
                <DocumentSelector
                  selectedDocuments={value.knowledge_documents || []}
                  onSelectionChange={(docIds) => {
                    onChange({
                      ...value,
                      knowledge_documents: docIds,
                    })
                  }}
                />
              </div>

              {/* 搜索模式 */}
              <div>
                <label className="block text-sm font-medium text-gray-900 mb-2">
                  搜索模式
                </label>
                <div className="space-y-2">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="radio"
                      value="document"
                      checked={(value.ragMode || 'document') === 'document'}
                      onChange={(e) =>
                        handleModeChange(e.target.value as 'document')
                      }
                      className="w-4 h-4"
                    />
                    <span className="text-sm text-gray-700">
                      📄 文档级（返回整个文档）
                    </span>
                  </label>
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="radio"
                      value="chunk"
                      checked={(value.ragMode || 'document') === 'chunk'}
                      onChange={(e) =>
                        handleModeChange(e.target.value as 'chunk')
                      }
                      className="w-4 h-4"
                    />
                    <span className="text-sm text-gray-700">
                      📍 分片级（返回匹配段落）
                    </span>
                  </label>
                </div>
              </div>

              {/* Top K */}
              <div>
                <label className="flex justify-between text-sm font-medium text-gray-900 mb-2">
                  <span>返回结果数: <strong>{value.topK || 5}</strong></span>
                  <span className="text-xs text-gray-500">最多 20</span>
                </label>
                <input
                  type="range"
                  min="1"
                  max="20"
                  value={value.topK || 5}
                  onChange={(e) => handleTopKChange(parseInt(e.target.value))}
                  className="w-full h-2 bg-gray-200 rounded-lg"
                />
              </div>

              {/* Min Score */}
              <div>
                <label className="flex justify-between text-sm font-medium text-gray-900 mb-2">
                  <span>相关性阈值: <strong>{(value.minScore || 0.5).toFixed(2)}</strong></span>
                  <span className="text-xs text-gray-500">0.0 - 1.0</span>
                </label>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.05"
                  value={value.minScore || 0.5}
                  onChange={(e) => handleMinScoreChange(parseFloat(e.target.value))}
                  className="w-full h-2 bg-gray-200 rounded-lg"
                />
              </div>

              {/* 上下文预览 */}
              <div>
                <label className="block text-sm font-medium text-gray-900 mb-2">
                  <span className="flex items-center gap-2">
                    上下文预览
                    {loadingContext && (
                      <Loader2 className="h-3 w-3 animate-spin" />
                    )}
                  </span>
                </label>
                {contextPreview ? (
                  <div className="bg-blue-50 border border-blue-200 rounded p-3 text-xs text-gray-700 max-h-24 overflow-auto font-mono whitespace-pre-wrap">
                    {contextPreview}
                  </div>
                ) : (
                  <p className="text-sm text-gray-500 italic bg-gray-50 p-2 rounded">
                    {loadingContext ? '加载中...' : '选择文档后预览上下文'}
                  </p>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* 提示信息 */}
      {value.enableRag && (
        <p className="text-xs text-blue-600 bg-blue-50 p-2 rounded">
          💡 启用 RAG 后，系统会在执行前检索相关文档并注入到 LLM 的提示词中
        </p>
      )}
    </div>
  )
}

