/**
 * Copilot API Client
 *
 * 与后端 Copilot 服务通信的客户端
 */

import axios, { AxiosInstance } from 'axios'
import {
  ChatRequest,
  ChatResponse,
  WorkflowSuggestionRequest,
  WorkflowSuggestionResponse,
  NodeSuggestionRequest,
  NodeSuggestionResponse,
  WorkflowDiagnosisRequest,
  WorkflowDiagnosisResponse,
  PromptGenerationRequest,
  PromptGenerationResponse,
} from '@/types/copilot'

class CopilotClient {
  private client: AxiosInstance

  constructor(baseURL?: string) {
    const apiBase =
      baseURL ||
      `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1`

    this.client = axios.create({
      baseURL: apiBase,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    // 添加请求拦截器，自动添加认证 token
    this.client.interceptors.request.use((config) => {
      const token = typeof window !== 'undefined' ? localStorage.getItem('accessToken') : null
      if (token) {
        config.headers.Authorization = `Bearer ${token}`
      }
      return config
    })
  }

  /**
   * Chat - 与 Copilot 对话
   */
  async chat(request: ChatRequest): Promise<ChatResponse> {
    try {
      const response = await this.client.post<ChatResponse>('/copilot/chat', request)
      return response.data
    } catch (error) {
      throw this._handleError(error, 'Chat request failed')
    }
  }

  /**
   * 建议工作流
   */
  async suggestWorkflow(
    request: WorkflowSuggestionRequest
  ): Promise<WorkflowSuggestionResponse> {
    try {
      const response = await this.client.post<WorkflowSuggestionResponse>(
        '/copilot/suggest/workflow',
        request
      )
      return response.data
    } catch (error) {
      throw this._handleError(error, 'Workflow suggestion failed')
    }
  }

  /**
   * 建议节点
   */
  async suggestNode(request: NodeSuggestionRequest): Promise<NodeSuggestionResponse> {
    try {
      const response = await this.client.post<NodeSuggestionResponse>(
        '/copilot/suggest/node',
        request
      )
      return response.data
    } catch (error) {
      throw this._handleError(error, 'Node suggestion failed')
    }
  }

  /**
   * 诊断工作流
   */
  async diagnoseWorkflow(request: WorkflowDiagnosisRequest): Promise<WorkflowDiagnosisResponse> {
    try {
      const response = await this.client.post<WorkflowDiagnosisResponse>(
        '/copilot/diagnose',
        request
      )
      return response.data
    } catch (error) {
      throw this._handleError(error, 'Workflow diagnosis failed')
    }
  }

  /**
   * 生成提示词
   */
  async generatePrompt(request: PromptGenerationRequest): Promise<PromptGenerationResponse> {
    try {
      const response = await this.client.post<PromptGenerationResponse>(
        '/copilot/generate-prompt',
        request
      )
      return response.data
    } catch (error) {
      throw this._handleError(error, 'Prompt generation failed')
    }
  }

  /**
   * 健康检查
   */
  async healthCheck(): Promise<{ status: string; service: string }> {
    try {
      const response = await this.client.get('/copilot/health')
      return response.data
    } catch (error) {
      throw this._handleError(error, 'Health check failed')
    }
  }

  /**
   * 错误处理
   */
  private _handleError(error: any, defaultMessage: string): never {
    if (error.response?.data?.detail) {
      throw new Error(error.response.data.detail)
    }
    if (error.message) {
      throw new Error(error.message)
    }
    throw new Error(defaultMessage)
  }
}

// 创建全局单例
export const copilotClient = new CopilotClient()

export default CopilotClient
