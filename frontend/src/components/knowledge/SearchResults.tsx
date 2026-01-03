/**
 * Search Results Component
 * 路径: frontend/src/components/knowledge/SearchResults.tsx
 */

'use client'

import React from 'react'
import { Card } from '@/components/ui/card'
import { Zap, Copy } from 'lucide-react'

interface SearchResult {
  id: string
  title?: string
  document_id?: string
  score: number
  content: string
  metadata?: Record<string, any>
}

interface SearchResultsProps {
  results: {
    data?: SearchResult[]
    results?: SearchResult[]
    query?: string
  }
}

export default function SearchResults({ results }: SearchResultsProps) {
  const items = results?.data || results?.results || []

  if (!items || items.length === 0) {
    return (
      <Card className="p-8 text-center bg-gray-50">
        <p className="text-gray-500">未找到相关结果</p>
      </Card>
    )
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2 mb-4">
        <Zap className="h-5 w-5 text-yellow-500" />
        <h3 className="font-semibold text-gray-900">
          搜索结果 ({items.length} 个)
        </h3>
      </div>

      {items.map((result, index) => (
        <Card key={result.id || index} className="p-4 hover:shadow-md transition-shadow">
          <div className="space-y-2">
            {/* 标题和相关性 */}
            <div className="flex justify-between items-start gap-2">
              <h4 className="font-medium text-gray-900">
                {result.title || `结果 ${index + 1}`}
              </h4>
              <div className="flex items-center gap-2">
                <span className="text-sm font-semibold text-green-600">
                  {Math.round(result.score * 100)}%
                </span>
                <div className="w-16 h-2 bg-gray-200 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-green-400 to-green-600 transition-all"
                    style={{ width: `${result.score * 100}%` }}
                  />
                </div>
              </div>
            </div>

            {/* 内容预览 */}
            <p className="text-sm text-gray-700 leading-relaxed line-clamp-3">
              {result.content}
            </p>

            {/* 元数据 */}
            {result.metadata && (
              <div className="flex flex-wrap gap-2 text-xs text-gray-500">
                {result.metadata.source && (
                  <span>📂 {result.metadata.source}</span>
                )}
                {result.metadata.section && (
                  <span>📌 {result.metadata.section}</span>
                )}
              </div>
            )}

            {/* 操作按钮 */}
            <button
              onClick={() => copyToClipboard(result.content)}
              className="text-xs text-blue-600 hover:text-blue-700 flex items-center gap-1 mt-2"
            >
              <Copy className="h-3 w-3" />
              复制内容
            </button>
          </div>
        </Card>
      ))}
    </div>
  )
}
