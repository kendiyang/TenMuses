/**
 * useCopilotStream Hook
 * 
 * 管理 Copilot 流式响应状态
 */

import { useState, useCallback, useRef } from 'react'
import { CopilotStreamClient, StreamEvent } from '@/lib/copilot-stream-client'

export interface UseCopilotStreamOptions {
  onMessageUpdate?: (content: string) => void
  onError?: (error: Error) => void
  onComplete?: () => void
}

export function useCopilotStream(options?: UseCopilotStreamOptions) {
  const [currentMessage, setCurrentMessage] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)
  const clientRef = useRef(new CopilotStreamClient())
  const abortControllerRef = useRef<AbortController | null>(null)

  const handleStreamEvent = useCallback((event: StreamEvent) => {
    switch (event.type) {
      case 'connected':
      case 'suggestion_started':
      case 'diagnosis_started':
        setCurrentMessage('')
        setError(null)
        break

      case 'token':
      case 'workflow':
      case 'suggestion_token':
      case 'diagnosis_token':
        if (event.content) {
          setCurrentMessage(prev => prev + event.content)
          options?.onMessageUpdate?.(currentMessage + event.content)
        }
        break

      case 'chat_completed':
      case 'suggestion_completed':
      case 'diagnosis_completed':
        setIsLoading(false)
        options?.onComplete?.()
        break

      case 'error':
        const err = new Error(event.message || 'Stream error')
        setError(err)
        setIsLoading(false)
        options?.onError?.(err)
        break

      default:
        // 处理任何其他包含 content 字段的事件类型
        if (event.content) {
          setCurrentMessage(prev => prev + event.content)
          options?.onMessageUpdate?.(currentMessage + event.content)
        }
        // 如果事件有 finished 标记为真，则完成
        if (event.finished === true) {
          setIsLoading(false)
          options?.onComplete?.()
        }
        break
    }
  }, [currentMessage, options])

  const streamChat = useCallback(
    async (threadId: string, message: string) => {
      try {
        setIsLoading(true)
        setCurrentMessage('')
        setError(null)

        abortControllerRef.current = new AbortController()
        await clientRef.current.streamChat(threadId, message, {
          signal: abortControllerRef.current.signal,
          onEvent: handleStreamEvent,
          onError: (err) => {
            setError(err)
            setIsLoading(false)
            options?.onError?.(err)
          },
          onComplete: () => {
            setIsLoading(false)
            options?.onComplete?.()
          },
        })
      } catch (err) {
        const error = err instanceof Error ? err : new Error(String(err))
        if (error.name !== 'AbortError') {
          setError(error)
          options?.onError?.(error)
        }
        setIsLoading(false)
      }
    },
    [handleStreamEvent, options]
  )

  const streamWorkflowSuggestions = useCallback(
    async (description: string, complexity?: string) => {
      try {
        setIsLoading(true)
        setCurrentMessage('')
        setError(null)

        abortControllerRef.current = new AbortController()
        await clientRef.current.streamWorkflowSuggestions(description, complexity, {
          signal: abortControllerRef.current.signal,
          onEvent: handleStreamEvent,
          onError: (err) => {
            setError(err)
            setIsLoading(false)
            options?.onError?.(err)
          },
          onComplete: () => {
            setIsLoading(false)
            options?.onComplete?.()
          },
        })
      } catch (err) {
        const error = err instanceof Error ? err : new Error(String(err))
        if (error.name !== 'AbortError') {
          setError(error)
          options?.onError?.(error)
        }
        setIsLoading(false)
      }
    },
    [handleStreamEvent, options]
  )

  const streamWorkflowDiagnosis = useCallback(
    async (nodes: any[], edges: any[]) => {
      try {
        setIsLoading(true)
        setCurrentMessage('')
        setError(null)

        abortControllerRef.current = new AbortController()
        await clientRef.current.streamWorkflowDiagnosis(nodes, edges, {
          signal: abortControllerRef.current.signal,
          onEvent: handleStreamEvent,
          onError: (err) => {
            setError(err)
            setIsLoading(false)
            options?.onError?.(err)
          },
          onComplete: () => {
            setIsLoading(false)
            options?.onComplete?.()
          },
        })
      } catch (err) {
        const error = err instanceof Error ? err : new Error(String(err))
        if (error.name !== 'AbortError') {
          setError(error)
          options?.onError?.(error)
        }
        setIsLoading(false)
      }
    },
    [handleStreamEvent, options]
  )

  const cancel = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }
    setIsLoading(false)
  }, [])

  const reset = useCallback(() => {
    setCurrentMessage('')
    setIsLoading(false)
    setError(null)
  }, [])

  return {
    currentMessage,
    isLoading,
    error,
    streamChat,
    streamWorkflowSuggestions,
    streamWorkflowDiagnosis,
    cancel,
    reset,
  }
}
