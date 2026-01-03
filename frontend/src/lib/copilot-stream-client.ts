/**
 * Copilot Stream Client
 * 
 * 处理 Server-Sent Events (SSE) 流式响应
 */

export interface StreamEvent {
  type: string
  [key: string]: any
}

export interface StreamOptions {
  headers?: Record<string, string>
  signal?: AbortSignal
  onEvent?: (event: StreamEvent) => void
  onError?: (error: Error) => void
  onComplete?: () => void
}

export class CopilotStreamClient {
  private baseURL: string

  constructor(baseURL: string = '/api/v1/copilot') {
    // 如果提供的是相对路径，需要添加后端URL前缀
    if (baseURL.startsWith('/')) {
      // 读取前端配置的 API 根地址，回退到当前页面 origin，再回退本地默认值
      const apiURL =
        (typeof process !== 'undefined' && process.env.NEXT_PUBLIC_API_URL) ||
        (typeof window !== 'undefined' ? `${window.location.origin.replace(/:\d+$/, ':8000')}` : 'http://localhost:8000')
      this.baseURL = `${apiURL}${baseURL}`
    } else {
      this.baseURL = baseURL
    }
  }

  private getToken(): string | null {
    if (typeof window === 'undefined') return null
    return localStorage.getItem('accessToken')
  }

  /**
   * 流式聊天
   */
  async streamChat(
    threadId: string,
    message: string,
    options?: StreamOptions
  ): Promise<void> {
    const url = new URL(`${this.baseURL}/chat/stream/${threadId}`)
    url.searchParams.set('message', message)

    await this.connectStream(url.toString(), options)
  }

  /**
   * 流式工作流建议
   */
  async streamWorkflowSuggestions(
    description: string,
    complexity: string = 'medium',
    options?: StreamOptions
  ): Promise<void> {
    const url = new URL(`${this.baseURL}/suggest/workflow/stream`)
    url.searchParams.set('description', description)
    url.searchParams.set('complexity', complexity)

    await this.connectStream(url.toString(), options)
  }

  /**
   * 流式工作流诊断
   */
  async streamWorkflowDiagnosis(
    nodes: any[],
    edges: any[],
    options?: StreamOptions
  ): Promise<void> {
    const url = `${this.baseURL}/diagnose/stream`

    const headers = {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${this.getToken()}`,
      ...options?.headers,
    }

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers,
        body: JSON.stringify({ nodes, edges }),
        signal: options?.signal,
      })

      if (!response.ok) {
        throw new Error(`Stream failed: ${response.status} ${response.statusText}`)
      }

      await this.handleStream(response, options)
    } catch (error) {
      if (options?.onError) {
        options.onError(error instanceof Error ? error : new Error(String(error)))
      }
      throw error
    }
  }

  /**
   * 连接流
   */
  private async connectStream(
    url: string,
    options?: StreamOptions
  ): Promise<void> {
    const headers = {
      'Authorization': `Bearer ${this.getToken()}`,
      ...options?.headers,
    }

    try {
      const response = await fetch(url, {
        method: 'GET',
        headers,
        signal: options?.signal,
      })

      if (!response.ok) {
        throw new Error(`Stream failed: ${response.status} ${response.statusText}`)
      }

      await this.handleStream(response, options)
    } catch (error) {
      if (options?.onError) {
        options.onError(error instanceof Error ? error : new Error(String(error)))
      }
      throw error
    }
  }

  /**
   * 处理流响应
   */
  private async handleStream(
    response: Response,
    options?: StreamOptions
  ): Promise<void> {
    const reader = response.body?.getReader()
    if (!reader) {
      throw new Error('Response body is not readable')
    }

    const decoder = new TextDecoder()
    let buffer = ''

    try {
      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        
        // 处理完整的行
        const lines = buffer.split('\n')
        buffer = lines.pop() || '' // 保留未完成的行

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))
              if (options?.onEvent) {
                options.onEvent(data)
              }
            } catch (e) {
              console.error('Failed to parse stream event:', line, e)
            }
          }
        }
      }

      // 处理剩余的缓冲区
      if (buffer && buffer.startsWith('data: ')) {
        try {
          const data = JSON.parse(buffer.slice(6))
          if (options?.onEvent) {
            options.onEvent(data)
          }
        } catch (e) {
          console.error('Failed to parse final stream event:', buffer, e)
        }
      }

      if (options?.onComplete) {
        options.onComplete()
      }
    } catch (error) {
      if (error instanceof Error && error.name !== 'AbortError') {
        if (options?.onError) {
          options.onError(error)
        }
        throw error
      }
    } finally {
      reader.releaseLock()
    }
  }
}

/**
 * 使用 Copilot 流式聊天的 Hook
 */
export function useStreamChat() {
  const client = new CopilotStreamClient()

  const streamChat = async (
    threadId: string,
    message: string,
    callbacks?: {
      onEvent?: (event: StreamEvent) => void
      onError?: (error: Error) => void
      onComplete?: () => void
    }
  ) => {
    return client.streamChat(threadId, message, {
      onEvent: callbacks?.onEvent,
      onError: callbacks?.onError,
      onComplete: callbacks?.onComplete,
    })
  }

  const streamWorkflowSuggestions = async (
    description: string,
    complexity?: string,
    callbacks?: {
      onEvent?: (event: StreamEvent) => void
      onError?: (error: Error) => void
      onComplete?: () => void
    }
  ) => {
    return client.streamWorkflowSuggestions(description, complexity, {
      onEvent: callbacks?.onEvent,
      onError: callbacks?.onError,
      onComplete: callbacks?.onComplete,
    })
  }

  const streamWorkflowDiagnosis = async (
    nodes: any[],
    edges: any[],
    callbacks?: {
      onEvent?: (event: StreamEvent) => void
      onError?: (error: Error) => void
      onComplete?: () => void
    }
  ) => {
    return client.streamWorkflowDiagnosis(nodes, edges, {
      onEvent: callbacks?.onEvent,
      onError: callbacks?.onError,
      onComplete: callbacks?.onComplete,
    })
  }

  return {
    streamChat,
    streamWorkflowSuggestions,
    streamWorkflowDiagnosis,
  }
}

export default CopilotStreamClient
