/**
 * RAG 搜索结果展示组件
 * 路径: frontend/src/components/workflow/RagSearchDisplay.tsx
 * 
 * 在工作流执行期间展示 RAG 搜索的实时结果
 */

'use client'

import React, { useMemo } from 'react'
import { Card } from '@/components/ui/card'
import {
  Search,
  Loader2,
  AlertCircle,
  CheckCircle2,
  Zap,
  File,
  Eye,
} from 'lucide-react'
import { RagResult, RagResultPayload, RagErrorPayload } from '@/types/websocket'

// 从 hook 中导入的状态类型
export interface RagSearchState {
  isSearching: boolean
  results: RagResultPayload | null
  error: RagErrorPayload | null
  query: string
  startTime: number | null
}

interface RagSearchDisplayProps {
  state: RagSearchState
  onResultClick?: (result: RagResult) => void
  highlightQuery?: boolean
}

/**
 * RAG 搜索结果显示组件
 * 
 * @example
 * <RagSearchDisplay 
 *   state={ragState}
 *   onResultClick={(result) => console.log(result)}
 *   highlightQuery={true}
 * />
 */
export function RagSearchDisplay({
  state,
  onResultClick,
  highlightQuery = true,
}: RagSearchDisplayProps) {
  const results = state.results?.results || []
  const durationSeconds = state.startTime
    ? ((Date.now() - state.startTime) / 1000).toFixed(2)
    : null

  const highlightedContent = useMemo(() => {
    if (!highlightQuery || !state.query || results.length === 0) {
      return null
    }

    return results.map((result: RagResult) => {
      const regex = new RegExp(`(${state.query})`, 'gi')
      return {
        ...result,
        highlightedContent: result.content.replace(regex, '<mark class="bg-yellow-200">$1</mark>'),
      }
    })
  }, [results, state.query, highlightQuery])

  // 搜索中状态
  if (state.isSearching && !results.length) {
    return (
      <Card className="p-6 bg-gradient-to-br from-blue-50 to-indigo-50 border border-blue-200">
        <div className="flex items-center gap-3 mb-4">
          <Loader2 className="h-5 w-5 text-blue-600 animate-spin" />
          <h3 className="font-semibold text-blue-900">RAG 搜索进行中...</h3>
        </div>
        {state.query && (
          <p className="text-sm text-blue-700">
            <strong>查询:</strong> {state.query}
          </p>
        )}
        {durationSeconds && (
          <p className="text-xs text-blue-600 mt-2">
            经过时间: {durationSeconds}s
          </p>
        )}
      </Card>
    )
  }

  // 错误状态
  if (state.error) {
    return (
      <Card className="p-6 bg-gradient-to-br from-red-50 to-orange-50 border border-red-200">
        <div className="flex items-start gap-3">
          <AlertCircle className="h-5 w-5 text-red-600 mt-0.5 flex-shrink-0" />
          <div>
            <h3 className="font-semibold text-red-900">搜索错误</h3>
            <p className="text-sm text-red-700 mt-1">{state.error.message}</p>
            {state.error.code && (
              <p className="text-xs text-red-600 mt-1">错误代码: {state.error.code}</p>
            )}
          </div>
        </div>
      </Card>
    )
  }

  // 无结果
  if (!state.isSearching && !results.length) {
    return (
      <Card className="p-6 text-center bg-gray-50">
        <Search className="h-8 w-8 text-gray-400 mx-auto mb-2" />
        <p className="text-gray-500 text-sm">等待 RAG 搜索结果...</p>
      </Card>
    )
  }

  // 显示结果
  return (
    <div className="space-y-3">
      {/* 搜索摘要 */}
      <Card className="p-4 bg-gradient-to-r from-green-50 to-emerald-50 border border-green-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="h-5 w-5 text-green-600" />
            <div>
              <h3 className="font-semibold text-green-900">搜索完成</h3>
              <p className="text-sm text-green-700 mt-0.5">
                找到 <strong>{results.length}</strong> 个相关结果
              </p>
            </div>
          </div>
          <div className="text-right">
            {state.results?.durationMs && (
              <p className="text-xs text-green-600">
                耗时: {(state.results.durationMs / 1000).toFixed(2)}s
              </p>
            )}
          </div>
        </div>
      </Card>

      {/* 搜索查询显示 */}
      {state.query && (
        <Card className="p-3 bg-blue-50 border border-blue-100">
          <p className="text-sm">
            <strong>查询:</strong> <em className="text-blue-700">{state.query}</em>
          </p>
        </Card>
      )}

      {/* 结果列表 */}
      <div className="space-y-3">
        {results.map((result: RagResult, index: number) => (
          <Card
            key={result.id}
            className="p-4 hover:shadow-md transition-shadow cursor-pointer overflow-hidden"
            onClick={() => onResultClick?.(result)}
          >
            {/* 结果头 */}
            <div className="flex items-start justify-between mb-2">
              <div className="flex items-center gap-2 flex-1">
                <File className="h-4 w-4 text-primary flex-shrink-0" />
                <h4 className="font-semibold text-gray-900 truncate">
                  {result.title || `结果 ${index + 1}`}
                </h4>
              </div>
              <div className="flex items-center gap-2 ml-2">
                <span className="inline-block px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded font-medium">
                  {(result.score * 100).toFixed(0)}%
                </span>
              </div>
            </div>

            {/* 内容预览 */}
            <p className="text-sm text-gray-600 line-clamp-2 mb-3">
              {result.content}
            </p>

            {/* 元数据 */}
            {result.metadata && (
              <div className="flex flex-wrap gap-2 text-xs text-gray-500">
                {Object.entries(result.metadata).map(([key, value]) => (
                  <span key={key} className="px-2 py-1 bg-gray-100 rounded">
                    {key}: {String(value)}
                  </span>
                ))}
              </div>
            )}

            {/* 分片索引 */}
            {result.chunkIndex !== undefined && (
              <div className="text-xs text-gray-400 mt-2">
                分片: #{result.chunkIndex}
              </div>
            )}
          </Card>
        ))}
      </div>
    </div>
  )
}

export default RagSearchDisplay
