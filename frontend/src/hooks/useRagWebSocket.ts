/**
 * RAG WebSocket 事件处理 Hook
 * 路径: frontend/src/hooks/useRagWebSocket.ts
 * 
 * 用于在工作流执行中集成 RAG 搜索事件
 */

import { useEffect, useCallback, useState } from 'react'
import { WebSocketClient } from '@/lib/websocket-client'
import {
  RagSearchStartedPayload,
  RagResultPayload,
  RagErrorPayload,
  RagCompletePayload,
  RagResult,
  WSEvent,
} from '@/types/websocket'

export interface RagSearchState {
  isSearching: boolean
  results: RagResultPayload | null
  error: RagErrorPayload | null
  query: string
  startTime: number | null
}

interface UseRagWebSocketOptions {
  threadId: string
  enabled?: boolean
  onSearchStarted?: (payload: RagSearchStartedPayload) => void
  onResultsReceived?: (payload: RagResultPayload) => void
  onSearchError?: (payload: RagErrorPayload) => void
  onSearchComplete?: (payload: RagCompletePayload) => void
}

/**
 * 自定义 Hook 用于处理 RAG WebSocket 事件
 * 
 * @example
 * const { state, subscribe, unsubscribe } = useRagWebSocket({
 *   threadId: 'xyz123',
 *   enabled: true,
 *   onResultsReceived: (results) => console.log(results)
 * })
 */
export function useRagWebSocket({
  threadId,
  enabled = true,
  onSearchStarted,
  onResultsReceived,
  onSearchError,
  onSearchComplete,
}: UseRagWebSocketOptions) {
  const [state, setState] = useState<RagSearchState>({
    isSearching: false,
    results: null,
    error: null,
    query: '',
    startTime: null,
  })

  const [wsClient] = useState(() => new WebSocketClient())

  // 处理搜索开始事件
  const handleSearchStarted = useCallback((event: WSEvent<RagSearchStartedPayload>) => {
    const payload = event.payload
    setState((prev) => ({
      ...prev,
      isSearching: true,
      query: payload.query,
      startTime: Date.now(),
      error: null,
    }))
    onSearchStarted?.(payload)
  }, [onSearchStarted])

  // 处理搜索结果事件
  const handleResult = useCallback((event: WSEvent<RagResultPayload>) => {
    const payload = event.payload
    setState((prev) => ({
      ...prev,
      results: payload,
    }))
    onResultsReceived?.(payload)
  }, [onResultsReceived])

  // 处理搜索错误事件
  const handleSearchError = useCallback((event: WSEvent<RagErrorPayload>) => {
    const payload = event.payload
    setState((prev) => ({
      ...prev,
      isSearching: false,
      error: payload,
    }))
    onSearchError?.(payload)
  }, [onSearchError])

  // 处理搜索完成事件
  const handleSearchComplete = useCallback((event: WSEvent<RagCompletePayload>) => {
    const payload = event.payload
    setState((prev) => ({
      ...prev,
      isSearching: false,
      startTime: null,
    }))
    onSearchComplete?.(payload)
  }, [onSearchComplete])

  // 连接 WebSocket 并订阅事件
  useEffect(() => {
    if (!enabled || !threadId) return

    const setupListeners = async () => {
      try {
        // 连接 WebSocket
        await wsClient.connect(threadId)

        // 订阅 RAG 事件
        wsClient.on('rag_search_started', handleSearchStarted)
        wsClient.on('rag_result', handleResult)
        wsClient.on('rag_error', handleSearchError)
        wsClient.on('rag_complete', handleSearchComplete)
      } catch (error) {
        console.error('Failed to setup WebSocket listeners:', error)
        setState((prev) => ({
          ...prev,
          error: {
            message: 'WebSocket 连接失败',
            code: 'WS_CONNECTION_ERROR',
            nodeId: 'rag',
          },
        }))
      }
    }

    setupListeners()

    // 清理函数
    return () => {
      wsClient.off('rag_search_started', handleSearchStarted)
      wsClient.off('rag_result', handleResult)
      wsClient.off('rag_error', handleSearchError)
      wsClient.off('rag_complete', handleSearchComplete)
    }
  }, [threadId, enabled, wsClient, handleSearchStarted, handleResult, handleSearchError, handleSearchComplete])

  return {
    state,
    wsClient,
    subscribe: (eventType: string, callback: (event: WSEvent) => void) => {
      wsClient.on(eventType, callback)
    },
    unsubscribe: (eventType: string, callback: (event: WSEvent) => void) => {
      wsClient.off(eventType, callback)
    },
  }
}

export default useRagWebSocket
