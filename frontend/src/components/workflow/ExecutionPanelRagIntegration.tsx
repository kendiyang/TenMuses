/**
 * 工作流执行面板中的 RAG 集成示例
 * 路径: frontend/src/components/workflow/ExecutionPanelRagIntegration.tsx
 * 
 * 这个组件展示如何在工作流执行中集成 RAG 搜索显示
 */

'use client'

import React, { useEffect, useState } from 'react'
import { Card } from '@/components/ui/card'
import RagSearchDisplay from './RagSearchDisplay'
import useRagWebSocket, { RagSearchState } from '@/hooks/useRagWebSocket'
import { MessageSquare, Zap } from 'lucide-react'

interface ExecutionPanelRagIntegrationProps {
  threadId: string | null
  isExecuting: boolean
}

/**
 * 工作流执行面板的 RAG 集成示例
 * 
 * 这个组件可以被集成到现有的 ExecutionPanel 中，
 * 用于在工作流运行时显示 RAG 搜索的实时结果
 */
export function ExecutionPanelRagIntegration({
  threadId,
  isExecuting,
}: ExecutionPanelRagIntegrationProps) {
  const [activeTab, setActiveTab] = useState('logs')
  
  // 使用 RAG WebSocket Hook
  const { state: ragState, wsClient } = useRagWebSocket({
    threadId: threadId || '',
    enabled: !!threadId && isExecuting,
    onSearchStarted: (payload) => {
      console.log('RAG Search Started:', payload)
      // 这里可以触发其他事件，如分析、日志记录等
    },
    onResultsReceived: (payload) => {
      console.log('RAG Results Received:', payload)
      // 自动切换到 RAG 标签页显示结果
      if (payload.results.length > 0) {
        setActiveTab('rag')
      }
    },
    onSearchError: (payload) => {
      console.error('RAG Search Error:', payload)
      setActiveTab('rag')
    },
    onSearchComplete: (payload) => {
      console.log('RAG Search Complete:', payload)
    },
  })

  return (
    <div className="w-full h-full flex flex-col space-y-4">
      {/* 标签页式的选择 */}
      <div className="flex gap-2 p-2 bg-gray-100 rounded-lg">
        <button
          onClick={() => setActiveTab('logs')}
          className={`flex items-center gap-2 px-4 py-2 rounded transition-colors ${
            activeTab === 'logs'
              ? 'bg-white text-gray-900 shadow'
              : 'text-gray-600 hover:bg-gray-50'
          }`}
        >
          <MessageSquare className="h-4 w-4" />
          执行日志
        </button>
        <button
          onClick={() => setActiveTab('rag')}
          className={`flex items-center gap-2 px-4 py-2 rounded transition-colors relative ${
            activeTab === 'rag'
              ? 'bg-white text-gray-900 shadow'
              : 'text-gray-600 hover:bg-gray-50'
          }`}
        >
          <Zap className="h-4 w-4" />
          RAG 搜索结果
          {ragState.results && (
            <span className="ml-2 px-2 py-0.5 bg-blue-100 text-blue-800 text-xs rounded-full">
              {ragState.results.results.length}
            </span>
          )}
        </button>
      </div>

      {/* 内容区域 */}
      <div className="flex-1 overflow-auto">
        {activeTab === 'logs' && (
          <Card className="p-4 text-sm text-gray-600">
            <p>执行日志将显示在这里...</p>
            <p className="text-xs text-gray-400 mt-2">
              WebSocket 连接状态: {wsClient.isConnected() ? '已连接' : '未连接'}
            </p>
          </Card>
        )}

        {activeTab === 'rag' && (
          <RagSearchDisplay
            state={ragState}
            onResultClick={(result) => {
              console.log('Clicked result:', result)
            }}
            highlightQuery={true}
          />
        )}
      </div>
    </div>
  )
}

export default ExecutionPanelRagIntegration
