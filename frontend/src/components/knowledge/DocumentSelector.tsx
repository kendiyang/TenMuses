/**
 * Document Selector Component
 * 用于 RAG 节点配置中选择文档
 * 路径: frontend/src/components/knowledge/DocumentSelector.tsx
 */

'use client'

import React, { useState, useEffect } from 'react'
import { Checkbox } from '@/components/ui/checkbox'
import { Card } from '@/components/ui/card'
import { Loader2, File, AlertCircle } from 'lucide-react'

interface Document {
  id: string
  title: string
  chunk_count: number
  status: 'pending' | 'processing' | 'completed' | 'failed'
}

interface DocumentSelectorProps {
  selectedDocuments?: string[]
  onSelectionChange?: (ids: string[]) => void
  multiSelect?: boolean
  showStatus?: boolean
}

export function DocumentSelector({
  selectedDocuments = [],
  onSelectionChange,
  multiSelect = true,
  showStatus = true,
}: DocumentSelectorProps) {
  const [documents, setDocuments] = useState<Document[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // 加载文档列表
  useEffect(() => {
    loadDocuments()
  }, [])

  const loadDocuments = async () => {
    try {
      setIsLoading(true)
      setError(null)

      const response = await fetch('/api/v1/kb/documents?status=completed', {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('accessToken')}`,
        },
      })

      if (!response.ok) {
        throw new Error('Failed to load documents')
      }

      const data = await response.json()
      setDocuments(data.data || [])
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to load documents'
      setError(errorMsg)
      console.error('Load documents error:', err)
    } finally {
      setIsLoading(false)
    }
  }

  const handleSelectDocument = (docId: string, checked: boolean) => {
    let newIds: string[]

    if (multiSelect) {
      // 多选模式
      newIds = checked
        ? [...selectedDocuments, docId]
        : selectedDocuments.filter((id) => id !== docId)
    } else {
      // 单选模式
      newIds = checked ? [docId] : []
    }

    onSelectionChange?.(newIds)
  }

  const getStatusBadge = (status: string) => {
    const styles: Record<string, string> = {
      pending: 'bg-yellow-100 text-yellow-800',
      processing: 'bg-blue-100 text-blue-800',
      completed: 'bg-green-100 text-green-800',
      failed: 'bg-red-100 text-red-800',
    }

    const labels: Record<string, string> = {
      pending: '待处理',
      processing: '处理中',
      completed: '已完成',
      failed: '失败',
    }

    return (
      <span className={`text-xs px-2 py-1 rounded-full ${styles[status] || 'bg-gray-100'}`}>
        {labels[status] || status}
      </span>
    )
  }

  if (isLoading) {
    return (
      <Card className="p-4 bg-gray-50">
        <div className="flex items-center justify-center gap-2 text-sm text-gray-600">
          <Loader2 className="h-4 w-4 animate-spin" />
          加载文档中...
        </div>
      </Card>
    )
  }

  if (error) {
    return (
      <Card className="p-4 bg-red-50 border border-red-200">
        <div className="flex gap-2 text-sm text-red-700">
          <AlertCircle className="h-4 w-4 flex-shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      </Card>
    )
  }

  if (documents.length === 0) {
    return (
      <Card className="p-4 bg-gray-50 text-center">
        <File className="h-8 w-8 text-gray-400 mx-auto mb-2" />
        <p className="text-sm text-gray-600">还没有已完成的文档</p>
      </Card>
    )
  }

  return (
    <Card className="p-3 bg-white border">
      <div className="space-y-2 max-h-[300px] overflow-y-auto">
        {documents.map((doc) => (
          <label
            key={doc.id}
            className="flex items-start gap-3 p-2 rounded hover:bg-gray-50 cursor-pointer transition-colors"
          >
            <Checkbox
              checked={selectedDocuments.includes(doc.id)}
              onCheckedChange={(checked: boolean) =>
                handleSelectDocument(doc.id, checked)
              }
              className="mt-1"
              disabled={!multiSelect && selectedDocuments.length > 0 && !selectedDocuments.includes(doc.id)}
            />

            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <File className="h-4 w-4 text-primary flex-shrink-0" />
                <span className="text-sm font-medium truncate">{doc.title}</span>
              </div>
              <div className="flex items-center gap-2 mt-1 text-xs text-gray-600">
                <span>📦 {doc.chunk_count} 个分片</span>
                {showStatus && getStatusBadge(doc.status)}
              </div>
            </div>
          </label>
        ))}
      </div>

      {selectedDocuments.length > 0 && (
        <div className="mt-3 pt-3 border-t text-xs text-gray-600">
          已选择 {selectedDocuments.length} 个文档
        </div>
      )}
    </Card>
  )
}
