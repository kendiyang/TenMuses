/**
 * CopilotHistory Component
 * 
 * 显示建议历史和收藏的面板
 */

'use client'

import React, { useState, useEffect, useRef } from 'react'
import { useSuggestionStorage } from '@/hooks/useSuggestionStorage'
import { type StoredSuggestion, type SuggestionFilter } from '@/lib/suggestion-storage'
import { Star, Trash2, Search, Filter, Download, Upload, Copy } from 'lucide-react'
import { cn } from '@/lib/utils'

export interface CopilotHistoryProps {
  onSelectSuggestion?: (suggestion: StoredSuggestion) => void
  onApply?: (suggestion: StoredSuggestion) => void
  className?: string
}

export function CopilotHistory({
  onSelectSuggestion,
  onApply,
  className,
}: CopilotHistoryProps) {
  const storage = useSuggestionStorage()
  
  const [suggestions, setSuggestions] = useState<StoredSuggestion[]>([])
  const [displayMode, setDisplayMode] = useState<'all' | 'favorites'>('all')
  const [searchText, setSearchText] = useState('')
  const [filterType, setFilterType] = useState<'workflow' | 'node' | 'all'>('all')
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [stats, setStats] = useState(storage.getStats())
  const searchTimeoutRef = useRef<NodeJS.Timeout>()

  // 初始加载和刷新
  useEffect(() => {
    refreshSuggestions()
    setStats(storage.getStats())
  }, [])

  // 搜索防抖
  useEffect(() => {
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current)
    }

    searchTimeoutRef.current = setTimeout(() => {
      refreshSuggestions()
    }, 300)

    return () => {
      if (searchTimeoutRef.current) clearTimeout(searchTimeoutRef.current)
    }
  }, [searchText, filterType, displayMode])

  const refreshSuggestions = () => {
    const filter: SuggestionFilter = {
      searchText: searchText || undefined,
      type: filterType !== 'all' ? (filterType as 'workflow' | 'node') : undefined,
      favorite: displayMode === 'favorites' ? true : undefined,
    }

    const results = storage.search(filter)
    setSuggestions(results)
    setStats(storage.getStats())
  }

  const handleToggleFavorite = (id: string) => {
    storage.toggleFavorite(id)
    refreshSuggestions()
  }

  const handleDelete = (id: string) => {
    if (confirm('确定要删除这条建议吗？')) {
      storage.remove(id)
      refreshSuggestions()
    }
  }

  const handleCopyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
    // 可选：显示复制成功提示
  }

  const handleExport = () => {
    const data = storage.export()
    const blob = new Blob([data], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `copilot-suggestions-${Date.now()}.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  const handleClearOld = () => {
    if (confirm('确定要删除 30 天前的建议吗？')) {
      const removed = storage.clearOld(30)
      refreshSuggestions()
      alert(`已删除 ${removed} 条旧建议`)
    }
  }

  return (
    <div className={cn('flex flex-col h-full bg-white rounded-lg', className)}>
      {/* 标题和模式切换 */}
      <div className="p-3 border-b space-y-2">
        <div className="flex items-center justify-between">
          <h3 className="font-semibold text-sm">建议历史</h3>
          <div className="flex gap-1">
            <button
              onClick={() => setDisplayMode('all')}
              className={cn(
                'px-2 py-1 text-xs rounded transition-colors',
                displayMode === 'all'
                  ? 'bg-purple-100 text-purple-700'
                  : 'text-gray-600 hover:text-gray-900'
              )}
            >
              全部
            </button>
            <button
              onClick={() => setDisplayMode('favorites')}
              className={cn(
                'px-2 py-1 text-xs rounded transition-colors flex items-center gap-1',
                displayMode === 'favorites'
                  ? 'bg-yellow-100 text-yellow-700'
                  : 'text-gray-600 hover:text-gray-900'
              )}
            >
              <Star className="h-3 w-3" />
              收藏
            </button>
          </div>
        </div>

        {/* 搜索框 */}
        <div className="flex gap-1">
          <div className="flex-1 relative">
            <Search className="absolute left-2 top-1/2 transform -translate-y-1/2 h-3 w-3 text-gray-400" />
            <input
              type="text"
              placeholder="搜索建议..."
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              className="w-full pl-6 pr-2 py-1 text-xs border border-gray-200 rounded focus:outline-none focus:ring-1 focus:ring-purple-500"
            />
          </div>
          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value as any)}
            className="px-2 py-1 text-xs border border-gray-200 rounded focus:outline-none focus:ring-1 focus:ring-purple-500"
          >
            <option value="all">全部类型</option>
            <option value="workflow">工作流</option>
            <option value="node">节点</option>
          </select>
        </div>

        {/* 统计信息 */}
        <div className="grid grid-cols-4 gap-1 text-xs">
          <div className="bg-gray-50 p-1 rounded text-center">
            <div className="font-bold text-gray-900">{stats.total}</div>
            <div className="text-gray-500">总数</div>
          </div>
          <div className="bg-yellow-50 p-1 rounded text-center">
            <div className="font-bold text-yellow-700">{stats.favorites}</div>
            <div className="text-gray-500">收藏</div>
          </div>
          <div className="bg-blue-50 p-1 rounded text-center">
            <div className="font-bold text-blue-700">{stats.workflows}</div>
            <div className="text-gray-500">工作流</div>
          </div>
          <div className="bg-green-50 p-1 rounded text-center">
            <div className="font-bold text-green-700">{stats.nodes}</div>
            <div className="text-gray-500">节点</div>
          </div>
        </div>
      </div>

      {/* 建议列表 */}
      <div className="flex-1 overflow-y-auto p-2 space-y-1">
        {suggestions.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-gray-500 py-8">
            <Search className="h-8 w-8 mb-2 opacity-50" />
            <p className="text-xs">
              {displayMode === 'favorites' ? '暂无收藏' : '暂无历史'}
            </p>
          </div>
        ) : (
          suggestions.map((suggestion) => (
            <div
              key={suggestion.id}
              onClick={() => {
                setSelectedId(suggestion.id)
                onSelectSuggestion?.(suggestion)
              }}
              className={cn(
                'p-2 rounded border transition-colors cursor-pointer',
                selectedId === suggestion.id
                  ? 'bg-purple-50 border-purple-200'
                  : 'bg-white border-gray-200 hover:bg-gray-50'
              )}
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex-1 min-w-0">
                  {/* 类型标签 */}
                  <div className="flex items-center gap-1 mb-1">
                    <span className={cn(
                      'px-1 py-0.5 text-xs rounded font-medium',
                      suggestion.type === 'workflow'
                        ? 'bg-blue-100 text-blue-700'
                        : 'bg-green-100 text-green-700'
                    )}>
                      {suggestion.type === 'workflow' ? '工作流' : '节点'}
                    </span>
                    <span className="text-xs text-gray-500">
                      {new Date(suggestion.timestamp).toLocaleDateString('zh-CN', {
                        month: 'short',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </span>
                  </div>

                  {/* 标题 */}
                  <p className="text-xs font-semibold text-gray-900 truncate">
                    {suggestion.content.name || suggestion.content.label || '未命名'}
                  </p>

                  {/* 描述 */}
                  {suggestion.content.description && (
                    <p className="text-xs text-gray-600 line-clamp-2">
                      {suggestion.content.description}
                    </p>
                  )}

                  {/* 标签 */}
                  {suggestion.tags && suggestion.tags.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-1">
                      {suggestion.tags.map((tag) => (
                        <span
                          key={tag}
                          className="text-xs px-1 py-0.5 bg-gray-200 text-gray-700 rounded"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  )}
                </div>

                {/* 操作按钮 */}
                <div className="flex gap-1 flex-shrink-0">
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      handleToggleFavorite(suggestion.id)
                    }}
                    className="p-1 hover:bg-yellow-100 rounded transition-colors"
                    title={suggestion.isFavorite ? '取消收藏' : '添加收藏'}
                  >
                    <Star
                      className={cn(
                        'h-3 w-3',
                        suggestion.isFavorite
                          ? 'fill-yellow-500 text-yellow-500'
                          : 'text-gray-400'
                      )}
                    />
                  </button>

                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      handleCopyToClipboard(JSON.stringify(suggestion.content, null, 2))
                    }}
                    className="p-1 hover:bg-blue-100 rounded transition-colors"
                    title="复制"
                  >
                    <Copy className="h-3 w-3 text-gray-400" />
                  </button>

                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      onApply?.(suggestion)
                    }}
                    className="p-1 hover:bg-green-100 rounded transition-colors text-green-600"
                    title="应用"
                  >
                    ✓
                  </button>

                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      handleDelete(suggestion.id)
                    }}
                    className="p-1 hover:bg-red-100 rounded transition-colors"
                    title="删除"
                  >
                    <Trash2 className="h-3 w-3 text-gray-400" />
                  </button>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* 底部操作栏 */}
      {suggestions.length > 0 && (
        <div className="border-t p-2 space-y-1 bg-gray-50">
          <button
            onClick={handleExport}
            className="w-full text-xs px-2 py-1 text-gray-700 bg-white border border-gray-200 rounded hover:bg-gray-100 transition-colors flex items-center justify-center gap-1"
          >
            <Download className="h-3 w-3" />
            导出
          </button>
          <button
            onClick={handleClearOld}
            className="w-full text-xs px-2 py-1 text-gray-700 bg-white border border-gray-200 rounded hover:bg-gray-100 transition-colors"
          >
            清除旧建议
          </button>
        </div>
      )}
    </div>
  )
}

export default CopilotHistory
