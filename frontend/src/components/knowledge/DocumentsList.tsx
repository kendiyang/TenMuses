/**
 * Documents List Component
 * 路径: frontend/src/components/knowledge/DocumentsList.tsx
 */

'use client'

import React from 'react'
import { format } from 'date-fns'
import { FileText, Loader2 } from 'lucide-react'

interface Document {
  id: string
  filename: string
  file_size: number
  created_at: string
  chunk_count: number
  status: 'pending' | 'processing' | 'completed' | 'failed'
}

interface DocumentsListProps {
  documents: Document[]
  selectedDocId: string | null
  onSelectDoc: (docId: string) => void
  isLoading?: boolean
}

export default function DocumentsList({
  documents,
  selectedDocId,
  onSelectDoc,
  isLoading = false,
}: DocumentsListProps) {
  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i]
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'text-green-600 bg-green-50'
      case 'processing':
        return 'text-blue-600 bg-blue-50'
      case 'failed':
        return 'text-red-600 bg-red-50'
      default:
        return 'text-gray-600 bg-gray-50'
    }
  }

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'completed':
        return '✅ 完成'
      case 'processing':
        return '⏳ 处理中'
      case 'failed':
        return '❌ 失败'
      default:
        return '⏸ 待处理'
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-32 text-gray-500">
        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
        <span>加载中...</span>
      </div>
    )
  }

  if (documents.length === 0) {
    return (
      <div className="flex items-center justify-center h-32 text-gray-500 text-sm">
        <p>暂无文档</p>
      </div>
    )
  }

  return (
    <div className="divide-y">
      {documents.map((doc) => (
        <div
          key={doc.id}
          className={`p-3 cursor-pointer hover:bg-blue-50 transition-colors ${
            selectedDocId === doc.id ? 'bg-blue-100 border-l-2 border-blue-500' : ''
          }`}
          onClick={() => onSelectDoc(doc.id)}
        >
          <div className="flex gap-2 items-start">
            <FileText className="h-4 w-4 mt-0.5 flex-shrink-0 text-gray-400" />
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-900 truncate">
                {doc.filename}
              </p>
              <p className="text-xs text-gray-500 mt-1">
                {formatFileSize(doc.file_size)} • {doc.chunk_count} 分片
              </p>
              <div className="flex items-center gap-2 mt-2">
                <span className={`text-xs px-2 py-0.5 rounded ${getStatusColor(doc.status)}`}>
                  {getStatusLabel(doc.status)}
                </span>
                <span className="text-xs text-gray-400">
                  {format(new Date(doc.created_at), 'MM-dd HH:mm')}
                </span>
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}
