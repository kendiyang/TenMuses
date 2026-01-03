/**
 * useCopilotChat Hook
 *
 * 管理 Copilot 聊天状态和逻辑
 */

import { useState, useCallback, useRef } from 'react'
import { copilotClient } from '@/services/copilot-client'
import { ChatMessage, ChatRequest } from '@/types/copilot'

interface UseCopilotChatOptions {
  onError?: (error: Error) => void
  onSuccess?: (message: string) => void
  maxHistoryLength?: number
}

export function useCopilotChat(options: UseCopilotChatOptions = {}) {
  const {
    onError,
    onSuccess,
    maxHistoryLength = 50,
  } = options

  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)
  const abortControllerRef = useRef<AbortController | null>(null)

  /**
   * 发送消息
   */
  const sendMessage = useCallback(
    async (content: string, context?: Record<string, any>) => {
      if (!content.trim()) {
        return
      }

      // 添加用户消息
      const userMessage: ChatMessage = {
        role: 'user',
        content: content.trim(),
        timestamp: Date.now(),
      }

      setMessages((prev) => [...prev, userMessage])
      setIsLoading(true)
      setError(null)

      try {
        // 构造请求
        const request: ChatRequest = {
          message: content,
          context: context || {},
          model: 'gpt-4o', // 使用 gpt-4o 模型
          chat_history: messages.map((m) => ({
            role: m.role,
            content: m.content,
          })),
        }

        // 调用 API
        const response = await copilotClient.chat(request)

        // 添加助手响应
        const assistantMessage: ChatMessage = {
          role: 'assistant',
          content: response.message,
          timestamp: Date.now(),
          suggestions: response.suggestions,
          diagnostics: response.diagnostics,
        }

        setMessages((prev) => {
          const newMessages = [...prev, assistantMessage]
          // 限制历史消息数量
          return newMessages.slice(-maxHistoryLength)
        })

        if (onSuccess) {
          onSuccess(response.message)
        }
      } catch (err) {
        const error = err instanceof Error ? err : new Error(String(err))
        setError(error)

        // 移除刚添加的用户消息（如果发送失败）
        setMessages((prev) => prev.slice(0, -1))

        if (onError) {
          onError(error)
        }
      } finally {
        setIsLoading(false)
      }
    },
    [messages, maxHistoryLength, onError, onSuccess]
  )

  /**
   * 清除历史
   */
  const clearHistory = useCallback(() => {
    setMessages([])
    setError(null)
  }, [])

  /**
   * 撤销最后一条消息
   */
  const undoLastMessage = useCallback(() => {
    setMessages((prev) => prev.slice(0, -2)) // 移除用户消息和助手消息
  }, [])

  /**
   * 重新发送最后一条消息
   */
  const resendLastMessage = useCallback(async () => {
    if (messages.length === 0) return

    // 找到最后一条用户消息
    let lastUserMessageIndex = -1
    for (let i = messages.length - 1; i >= 0; i--) {
      if (messages[i].role === 'user') {
        lastUserMessageIndex = i
        break
      }
    }

    if (lastUserMessageIndex === -1) return

    const lastUserMessage = messages[lastUserMessageIndex]

    // 移除最后的消息对（用户 + 助手）
    setMessages((prev) => prev.slice(0, lastUserMessageIndex))

    // 重新发送
    await sendMessage(lastUserMessage.content)
  }, [messages, sendMessage])

  /**
   * 取消请求
   */
  const cancel = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }
  }, [])

  return {
    messages,
    isLoading,
    error,
    sendMessage,
    clearHistory,
    undoLastMessage,
    resendLastMessage,
    cancel,
  }
}

export default useCopilotChat
