/**
 * Search Section Component  
 * 路径: frontend/src/components/knowledge/SearchSection.tsx
 */

'use client'

import React, { useState } from 'react'
import { Card } from '@/components/ui/card'
import { Search, Loader2 } from 'lucide-react'

interface SearchSectionProps {
  onSearch: (
    query: string,
    mode: 'document' | 'chunk',
    topK: number,
    minScore: number
  ) => void
  isLoading?: boolean
  disabled?: boolean
}

export default function SearchSection({
  onSearch,
  isLoading = false,
  disabled = false,
}: SearchSectionProps) {
  const [query, setQuery] = useState('')
  const [searchMode, setSearchMode] = useState<'document' | 'chunk'>('document')
  const [topK, setTopK] = useState(5)
  const [minScore, setMinScore] = useState(0.5)

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!query.trim()) return
    onSearch(query, searchMode, topK, minScore)
  }

  return (
    <Card className="p-6 border-l-4 border-l-purple-500">
      <div className="space-y-4">
        <div className="flex items-center gap-2 mb-4">
          <Search className="h-5 w-5 text-purple-600" />
          <h3 className="font-semibold text-gray-900">语义搜索</h3>
        </div>

        <form onSubmit={handleSearch} className="space-y-4">
          {/* 搜索输入 */}
          <div>
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="输入搜索关键词..."
              disabled={disabled || isLoading}
              className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 disabled:bg-gray-100"
            />
          </div>

          {/* 搜索模式选择 */}
          <div className="grid grid-cols-2 gap-3">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="radio"
                value="document"
                checked={searchMode === 'document'}
                onChange={(e) => setSearchMode(e.target.value as 'document')}
                disabled={disabled || isLoading}
                className="w-4 h-4"
              />
              <span className="text-sm text-gray-700">
                📄 文档级搜索
                <span className="block text-xs text-gray-500 mt-0.5">返回整个文档</span>
              </span>
            </label>

            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="radio"
                value="chunk"
                checked={searchMode === 'chunk'}
                onChange={(e) => setSearchMode(e.target.value as 'chunk')}
                disabled={disabled || isLoading}
                className="w-4 h-4"
              />
              <span className="text-sm text-gray-700">
                📍 分片级搜索
                <span className="block text-xs text-gray-500 mt-0.5">返回匹配段落</span>
              </span>
            </label>
          </div>

          {/* 参数调整 */}
          <div className="border-t pt-4 space-y-3">
            {/* Top K */}
            <div>
              <label className="flex justify-between text-sm text-gray-700 mb-2">
                <span>返回结果数量: <strong>{topK}</strong></span>
                <span className="text-xs text-gray-500">最多 20 个</span>
              </label>
              <input
                type="range"
                min="1"
                max="20"
                value={topK}
                onChange={(e) => setTopK(parseInt(e.target.value))}
                disabled={disabled || isLoading}
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer disabled:opacity-50"
              />
            </div>

            {/* Min Score */}
            <div>
              <label className="flex justify-between text-sm text-gray-700 mb-2">
                <span>相关性阈值: <strong>{minScore.toFixed(2)}</strong></span>
                <span className="text-xs text-gray-500">0.0 - 1.0</span>
              </label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={minScore}
                onChange={(e) => setMinScore(parseFloat(e.target.value))}
                disabled={disabled || isLoading}
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer disabled:opacity-50"
              />
              <p className="text-xs text-gray-500 mt-1">
                只返回相关性大于 {minScore.toFixed(2)} 的结果
              </p>
            </div>
          </div>

          {/* 提交按钮 */}
          <button
            type="submit"
            disabled={!query.trim() || disabled || isLoading}
            className="w-full px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:bg-gray-400 transition-colors flex items-center justify-center gap-2"
          >
            {isLoading && <Loader2 className="h-4 w-4 animate-spin" />}
            {isLoading ? '搜索中...' : '🔍 搜索'}
          </button>
        </form>

        {disabled && (
          <p className="text-sm text-amber-600 bg-amber-50 p-2 rounded">
            💡 请先上传文档后进行搜索
          </p>
        )}
      </div>
    </Card>
  )
}
