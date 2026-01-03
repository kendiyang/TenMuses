/**
 * CopilotStreamDisplay Component
 * 
 * 实时显示流式响应内容
 */

'use client'

import React, { useEffect, useRef } from 'react'
import { Loader2, AlertCircle, Check } from 'lucide-react'

export interface CopilotStreamDisplayProps {
  content: string
  isLoading: boolean
  error?: Error | null
  onCancel?: () => void
  className?: string
}

export function CopilotStreamDisplay({
  content,
  isLoading,
  error,
  onCancel,
  className = '',
}: CopilotStreamDisplayProps) {
  const scrollRef = useRef<HTMLDivElement>(null)
  const contentRef = useRef<HTMLDivElement>(null)

  // 自动滚动到底部
  useEffect(() => {
    if (contentRef.current) {
      contentRef.current.scrollIntoView({ behavior: 'smooth', block: 'end' })
    }
  }, [content])

  return (
    <div className={`space-y-3 ${className}`}>
      {/* 内容区域 */}
      <div
        ref={scrollRef}
        className="bg-gray-50 rounded-lg p-4 min-h-[100px] max-h-[400px] overflow-y-auto border border-gray-200"
      >
        {content ? (
          <div
            ref={contentRef}
            className="text-sm text-gray-800 whitespace-pre-wrap leading-relaxed font-sans"
          >
            {content}
            {isLoading && (
              <span className="inline-block w-2 h-5 ml-1 bg-blue-500 animate-pulse"></span>
            )}
          </div>
        ) : error ? (
          <div className="flex items-start gap-3 text-sm text-red-700">
            <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold">Error</p>
              <p className="text-red-600">{error.message}</p>
            </div>
          </div>
        ) : isLoading ? (
          <div className="flex items-center gap-2 text-gray-500">
            <Loader2 className="w-4 h-4 animate-spin" />
            <span className="text-sm">等待响应中...</span>
          </div>
        ) : (
          <p className="text-gray-400 text-sm">等待输入...</p>
        )}
      </div>

      {/* 控制按钮 */}
      {isLoading && (
        <div className="flex gap-2 justify-end">
          <button
            onClick={onCancel}
            className="px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          >
            取消
          </button>
        </div>
      )}

      {/* 完成指示 */}
      {!isLoading && content && !error && (
        <div className="flex items-center gap-2 text-xs text-green-600">
          <Check className="w-4 h-4" />
          <span>响应完成</span>
        </div>
      )}

      {/* 令牌计数 (仅在有内容时显示) */}
      {content && (
        <div className="text-xs text-gray-500">
          字符数: {content.length} | 估计令牌: {Math.ceil(content.length / 4)}
        </div>
      )}
    </div>
  )
}

export default CopilotStreamDisplay
