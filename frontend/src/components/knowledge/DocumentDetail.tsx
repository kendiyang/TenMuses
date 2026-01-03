/**
 * Document Detail Component
 * 路径: frontend/src/components/knowledge/DocumentDetail.tsx
 */

'use client'

import React, { useState, useEffect } from 'react'
import { Card } from '@/components/ui/card'
import { FileText, Trash2, ChevronDown, ChevronUp, Loader2 } from 'lucide-react'
import { format } from 'date-fns'

interface DocumentChunk {
  id: string
  chunk_index: number
  content: string
  token_count: number
}

interface DocumentDetailProps {
  documentId: string
  onDeleted?: (docId: string) => void
}

export default function DocumentDetail({
  documentId,
  onDeleted,
}: DocumentDetailProps) {
  const [document, setDocument] = useState<any | null>(null)
  const [chunks, setChunks] = useState<DocumentChunk[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [expandedChunkId, setExpandedChunkId] = useState<string | null>(null)
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  const [isDeleting, setIsDeleting] = useState(false)

  useEffect(() => {
    loadDocument()
  }, [documentId])

  const loadDocument = async () => {
    try {
      setIsLoading(true)
      
      // 这里需要根据实际 API 调整，目前假设返回文档列表
      const response = await fetch(`/api/v1/kb/documents`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('accessToken')}`,
        },
      })

      if (!response.ok) throw new Error('Failed to load document')

      const data = await response.json()
      const doc = (data.data || []).find((d: any) => d.id === documentId)
      
      if (doc) {
        setDocument(doc)
        // 提取分片信息（后续可以通过专门 API 获取）
        setChunks([])
      }
    } catch (err) {
      console.error('Load document error:', err)
    } finally {
      setIsLoading(false)
    }
  }

  const handleDelete = async () => {
    try {
      setIsDeleting(true)
      const response = await fetch(`/api/v1/kb/documents/${documentId}`, {
        method: 'DELETE',
        headers: {
          Authorization: `Bearer ${localStorage.getItem('accessToken')}`,
        },
      })

      if (!response.ok) throw new Error('Failed to delete document')

      onDeleted?.(documentId)
      setShowDeleteConfirm(false)
    } catch (err) {
      console.error('Delete document error:', err)
      alert('删除失败，请重试')
    } finally {
      setIsDeleting(false)
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i]
  }

  if (isLoading) {
    return (
      <Card className="h-full flex items-center justify-center">
        <Loader2 className="h-5 w-5 animate-spin text-gray-500" />
      </Card>
    )
  }

  if (!document) {
    return (
      <Card className="h-full flex items-center justify-center">
        <p className="text-gray-500">未找到文档</p>
      </Card>
    )
  }

  return (
    <Card className="h-full overflow-auto flex flex-col">
      {/* 文档头信息 */}
      <div className="bg-gray-50 border-b p-4 sticky top-0">
        <div className="flex items-start gap-3">
          <FileText className="h-6 w-6 text-gray-400 flex-shrink-0 mt-1" />
          <div className="flex-1 min-w-0">
            <h3 className="font-semibold text-gray-900 truncate">
              {document.filename}
            </h3>
            <p className="text-xs text-gray-500 mt-1">
              {formatFileSize(document.file_size)} • {document.chunk_count} 分片
            </p>
          </div>
        </div>
      </div>

      {/* 文档详情 */}
      <div className="flex-1 p-4 space-y-4 overflow-auto">
        {/* 元数据 */}
        <div className="space-y-3 text-sm">
          <div>
            <p className="text-gray-600">状态</p>
            <p className="font-medium text-gray-900 mt-1">
              {document.status === 'completed' && '✅ 已完成'}
              {document.status === 'processing' && '⏳ 处理中'}
              {document.status === 'failed' && '❌ 失败'}
              {document.status === 'pending' && '⏸ 待处理'}
            </p>
          </div>

          <div>
            <p className="text-gray-600">上传时间</p>
            <p className="font-medium text-gray-900 mt-1">
              {format(new Date(document.created_at), 'yyyy-MM-dd HH:mm:ss')}
            </p>
          </div>

          {document.processed_at && (
            <div>
              <p className="text-gray-600">处理时间</p>
              <p className="font-medium text-gray-900 mt-1">
                {format(new Date(document.processed_at), 'yyyy-MM-dd HH:mm:ss')}
              </p>
            </div>
          )}

          {document.metadata && Object.keys(document.metadata).length > 0 && (
            <div>
              <p className="text-gray-600">元数据</p>
              <div className="mt-2 bg-gray-50 rounded p-2 text-xs font-mono">
                {JSON.stringify(document.metadata, null, 2)}
              </div>
            </div>
          )}
        </div>

        {/* 分片列表 */}
        {chunks.length > 0 && (
          <div className="border-t pt-4">
            <h4 className="font-semibold text-gray-900 mb-3">分片列表</h4>
            <div className="space-y-2">
              {chunks.map((chunk) => (
                <div key={chunk.id} className="border rounded">
                  <button
                    onClick={() =>
                      setExpandedChunkId(
                        expandedChunkId === chunk.id ? null : chunk.id
                      )
                    }
                    className="w-full flex items-center gap-2 p-2 hover:bg-gray-50"
                  >
                    {expandedChunkId === chunk.id ? (
                      <ChevronUp className="h-4 w-4 text-gray-400" />
                    ) : (
                      <ChevronDown className="h-4 w-4 text-gray-400" />
                    )}
                    <span className="text-xs font-medium text-gray-700">
                      分片 {chunk.chunk_index + 1}
                    </span>
                    <span className="text-xs text-gray-500">
                      ({chunk.token_count} tokens)
                    </span>
                  </button>

                  {expandedChunkId === chunk.id && (
                    <div className="border-t p-2 bg-gray-50 text-xs text-gray-700 max-h-32 overflow-auto">
                      {chunk.content}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* 底部操作按钮 */}
      <div className="border-t p-4 bg-gray-50 sticky bottom-0">
        {showDeleteConfirm ? (
          <div className="space-y-2">
            <p className="text-sm text-gray-700">确定删除此文档？</p>
            <div className="flex gap-2">
              <button
                onClick={handleDelete}
                disabled={isDeleting}
                className="flex-1 px-3 py-2 bg-red-600 text-white rounded hover:bg-red-700 disabled:bg-gray-400 text-sm font-medium"
              >
                {isDeleting ? '删除中...' : '确认删除'}
              </button>
              <button
                onClick={() => setShowDeleteConfirm(false)}
                disabled={isDeleting}
                className="flex-1 px-3 py-2 bg-gray-200 text-gray-800 rounded hover:bg-gray-300 disabled:opacity-50 text-sm font-medium"
              >
                取消
              </button>
            </div>
          </div>
        ) : (
          <button
            onClick={() => setShowDeleteConfirm(true)}
            className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-red-50 text-red-600 rounded hover:bg-red-100 transition-colors"
          >
            <Trash2 className="h-4 w-4" />
            <span className="text-sm font-medium">删除文档</span>
          </button>
        )}
      </div>
    </Card>
  )
}
