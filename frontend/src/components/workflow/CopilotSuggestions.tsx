/**
 * CopilotSuggestions Component
 *
 * 显示 Copilot 返回的工作流和节点建议
 */

import React, { useState } from 'react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Zap, Check, ChevronDown } from 'lucide-react'
import { cn } from '@/lib/utils'

export interface CopilotSuggestionsProps {
  suggestions?: Array<{
    type: 'workflow' | 'node'
    id: string
    name?: string
    description?: string
    nodeCount?: number
    edgeCount?: number
    nodeType?: string
    label?: string
    explanation?: string
    data?: any
  }>
  onApply?: (suggestion: any) => void
  loading?: boolean
  className?: string
}

/**
 * 建议卡片组件
 * 
 * 功能:
 * - 显示工作流建议列表
 * - 显示节点建议列表
 * - 处理应用操作（带加载状态）
 * - 显示应用成功反馈
 */
export function CopilotSuggestions({
  suggestions = [],
  onApply,
  loading,
  className,
}: CopilotSuggestionsProps) {
  const [appliedId, setAppliedId] = useState<string | null>(null)
  const [isExpanded, setIsExpanded] = useState(true)

  if (!suggestions || suggestions.length === 0) return null

  const workflowSuggestions = suggestions.filter((s) => s.type === 'workflow')
  const nodeSuggestions = suggestions.filter((s) => s.type === 'node')

  const handleApply = (suggestion: any) => {
    onApply?.(suggestion)
    setAppliedId(suggestion.id)
    // 重置反馈状态
    setTimeout(() => setAppliedId(null), 2000)
  }

  return (
    <div className={cn('border-t bg-gradient-to-b from-blue-50 to-transparent', className)}>
      {/* 标题栏 */}
      <div
        className="flex items-center justify-between p-3 cursor-pointer hover:bg-blue-100 transition-colors"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center gap-2">
          <Zap className="w-4 h-4 text-blue-600" />
          <h4 className="font-semibold text-gray-900 text-sm">建议</h4>
          <Badge variant="secondary" className="text-xs">
            {suggestions.length}
          </Badge>
        </div>
        <ChevronDown
          className={cn('w-4 h-4 text-gray-500 transition-transform', isExpanded && 'rotate-180')}
        />
      </div>

      {/* 建议内容 */}
      {isExpanded && (
        <div className="space-y-3 p-3">
          {/* 工作流建议 */}
          {workflowSuggestions.length > 0 && (
            <div className="space-y-2">
              <h5 className="text-xs font-semibold text-gray-700 uppercase tracking-wide">工作流建议</h5>
              {workflowSuggestions.map((wf) => {
                const isApplied = appliedId === wf.id

                return (
                  <Card
                    key={wf.id}
                    className={cn(
                      'p-3 transition-all',
                      isApplied
                        ? 'bg-green-50 border-green-300 ring-1 ring-green-200'
                        : 'bg-white hover:shadow-md cursor-pointer hover:border-blue-300'
                    )}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex-1 min-w-0">
                        <h6 className="text-xs font-semibold text-gray-900 truncate flex items-center gap-1">
                          📋 {wf.name}
                        </h6>
                        <p className="text-xs text-gray-600 line-clamp-2 mt-1">{wf.description}</p>
                        <div className="flex items-center gap-2 mt-1 text-xs text-gray-500">
                          <span>{wf.nodeCount || 0} 节点</span>
                          <span>•</span>
                          <span>{wf.edgeCount || 0} 连接</span>
                        </div>
                      </div>
                      <Button
                        size="sm"
                        variant={isApplied ? 'default' : 'outline'}
                        onClick={() => handleApply(wf)}
                        disabled={loading}
                        className="flex-shrink-0 text-xs h-7"
                      >
                        {isApplied ? <Check className="w-3 h-3" /> : '应用'}
                      </Button>
                    </div>
                  </Card>
                )
              })}
            </div>
          )}

          {/* 节点建议 */}
          {nodeSuggestions.length > 0 && (
            <div className="space-y-2">
              <h5 className="text-xs font-semibold text-gray-700 uppercase tracking-wide">节点建议</h5>
              {nodeSuggestions.map((node) => {
                const isApplied = appliedId === node.id

                return (
                  <Card
                    key={node.id}
                    className={cn(
                      'p-3 transition-all',
                      isApplied
                        ? 'bg-green-50 border-green-300 ring-1 ring-green-200'
                        : 'bg-white hover:shadow-md cursor-pointer hover:border-green-300'
                    )}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <Badge variant="outline" className="text-xs">
                            ⚙️ {node.nodeType}
                          </Badge>
                          {node.label && (
                            <h6 className="text-xs font-semibold text-gray-900 truncate">{node.label}</h6>
                          )}
                        </div>
                        <p className="text-xs text-gray-600 mt-1 line-clamp-2">{node.explanation}</p>
                      </div>
                      <Button
                        size="sm"
                        variant={isApplied ? 'default' : 'outline'}
                        onClick={() => handleApply(node)}
                        disabled={loading}
                        className="flex-shrink-0 text-xs h-7 w-7 p-0"
                      >
                        {isApplied ? <Check className="w-3 h-3" /> : '+'}
                      </Button>
                    </div>
                  </Card>
                )
              })}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default CopilotSuggestions
