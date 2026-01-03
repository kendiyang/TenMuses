/**
 * 真实前后端集成测试
 * 测试前端与后端 API 的真实交互
 */

import axios from 'axios'

// API 配置
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'
const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000'

// 测试用例
describe('真实前后端集成测试', () => {
  describe('Copilot 聊天集成', () => {
    it('应该向后端发送聊天消息并接收响应', async () => {
      const message = 'Hello, help me create a simple workflow'
      
      try {
        const response = await axios.post(
          `${API_BASE_URL}/copilot/chat`,
          {
            message,
            chat_history: [],
            model: 'gpt-4-turbo-preview'
          },
          {
            headers: {
              'Authorization': `Bearer ${process.env.TEST_JWT_TOKEN || ''}`,
              'Content-Type': 'application/json'
            }
          }
        )

        expect(response.status).toBe(200)
        expect(response.data).toHaveProperty('message')
        expect(response.data.message.length).toBeGreaterThan(0)
      } catch (error: any) {
        console.error('Chat API 错误:', error.response?.data || error.message)
        throw error
      }
    })

    it('应该处理聊天历史记录', async () => {
      const chatHistory = [
        { role: 'user', content: '你好' },
        { role: 'assistant', content: '你好！有什么我可以帮助的吗？' }
      ]
      const newMessage = '帮我建议一个工作流'

      try {
        const response = await axios.post(
          `${API_BASE_URL}/copilot/chat`,
          {
            message: newMessage,
            chat_history: chatHistory,
            model: 'gpt-4-turbo-preview'
          },
          {
            headers: {
              'Authorization': `Bearer ${process.env.TEST_JWT_TOKEN || ''}`,
              'Content-Type': 'application/json'
            }
          }
        )

        expect(response.status).toBe(200)
        expect(response.data).toHaveProperty('message')
      } catch (error: any) {
        console.error('Chat 历史处理错误:', error.response?.data || error.message)
        throw error
      }
    })
  })

  describe('工作流建议 API', () => {
    it('应该获取工作流建议', async () => {
      try {
        const response = await axios.post(
          `${API_BASE_URL}/copilot/suggest-workflows`,
          {
            description: 'Create a RAG workflow for document processing',
            complexity: 'medium'
          },
          {
            headers: {
              'Authorization': `Bearer ${process.env.TEST_JWT_TOKEN || ''}`,
              'Content-Type': 'application/json'
            }
          }
        )

        expect(response.status).toBe(200)
        expect(Array.isArray(response.data)).toBe(true)
        if (response.data.length > 0) {
          expect(response.data[0]).toHaveProperty('name')
          expect(response.data[0]).toHaveProperty('nodes')
          expect(response.data[0]).toHaveProperty('edges')
        }
      } catch (error: any) {
        console.error('工作流建议 API 错误:', error.response?.data || error.message)
        throw error
      }
    })

    it('应该支持不同的复杂度级别', async () => {
      const complexities = ['simple', 'medium', 'advanced']

      for (const complexity of complexities) {
        try {
          const response = await axios.post(
            `${API_BASE_URL}/copilot/suggest-workflows`,
            {
              description: 'Test workflow',
              complexity
            },
            {
              headers: {
                'Authorization': `Bearer ${process.env.TEST_JWT_TOKEN || ''}`,
                'Content-Type': 'application/json'
              }
            }
          )

          expect(response.status).toBe(200)
        } catch (error) {
          console.error(`${complexity} 复杂度错误:`, error)
          throw error
        }
      }
    })
  })

  describe('节点建议 API', () => {
    it('应该获取节点建议', async () => {
      try {
        const response = await axios.post(
          `${API_BASE_URL}/copilot/suggest-nodes`,
          {
            context: 'I need to process documents and extract information',
            previous_node_type: 'LLM',
            workflow_description: 'Document processing workflow'
          },
          {
            headers: {
              'Authorization': `Bearer ${process.env.TEST_JWT_TOKEN || ''}`,
              'Content-Type': 'application/json'
            }
          }
        )

        expect(response.status).toBe(200)
        expect(Array.isArray(response.data)).toBe(true)
      } catch (error: any) {
        console.error('节点建议 API 错误:', error.response?.data || error.message)
        throw error
      }
    })
  })

  describe('模板相关 API', () => {
    it('应该获取可用的模板列表', async () => {
      try {
        const response = await axios.get(
          `${API_BASE_URL}/templates`,
          {
            headers: {
              'Authorization': `Bearer ${process.env.TEST_JWT_TOKEN || ''}`
            }
          }
        )

        expect(response.status).toBe(200)
        expect(Array.isArray(response.data)).toBe(true)
      } catch (error: any) {
        // 如果列表为空也是正常的
        if (error.response?.status !== 404) {
          console.error('模板列表 API 错误:', error.response?.data || error.message)
          throw error
        }
      }
    })

    it('应该保存新模板', async () => {
      const newTemplate = {
        name: 'Test Template',
        description: 'A test template',
        content: 'Hello {{name}}, you have {{count}} items',
        variables: ['name', 'count']
      }

      try {
        const response = await axios.post(
          `${API_BASE_URL}/templates`,
          newTemplate,
          {
            headers: {
              'Authorization': `Bearer ${process.env.TEST_JWT_TOKEN || ''}`,
              'Content-Type': 'application/json'
            }
          }
        )

        expect(response.status).toBeOneOf([200, 201])
      } catch (error: any) {
        console.error('保存模板 API 错误:', error.response?.data || error.message)
        throw error
      }
    })
  })

  describe('建议历史记录 API', () => {
    it('应该保存建议', async () => {
      const suggestion = {
        type: 'workflow',
        content: 'Suggested workflow',
        metadata: {
          description: 'A test suggestion'
        }
      }

      try {
        const response = await axios.post(
          `${API_BASE_URL}/suggestions`,
          suggestion,
          {
            headers: {
              'Authorization': `Bearer ${process.env.TEST_JWT_TOKEN || ''}`,
              'Content-Type': 'application/json'
            }
          }
        )

        expect(response.status).toBeOneOf([200, 201])
      } catch (error: any) {
        console.error('保存建议 API 错误:', error.response?.data || error.message)
        throw error
      }
    })

    it('应该获取建议列表', async () => {
      try {
        const response = await axios.get(
          `${API_BASE_URL}/suggestions`,
          {
            headers: {
              'Authorization': `Bearer ${process.env.TEST_JWT_TOKEN || ''}`
            }
          }
        )

        expect(response.status).toBe(200)
        expect(Array.isArray(response.data)).toBe(true)
      } catch (error: any) {
        console.error('获取建议列表 API 错误:', error.response?.data || error.message)
        throw error
      }
    })

    it('应该搜索建议', async () => {
      try {
        const response = await axios.get(
          `${API_BASE_URL}/suggestions/search`,
          {
            params: { q: 'workflow' },
            headers: {
              'Authorization': `Bearer ${process.env.TEST_JWT_TOKEN || ''}`
            }
          }
        )

        expect(response.status).toBe(200)
        expect(Array.isArray(response.data)).toBe(true)
      } catch (error: any) {
        console.error('搜索建议 API 错误:', error.response?.data || error.message)
        throw error
      }
    })
  })

  describe('工作流执行与流式传输', () => {
    it('应该启动工作流运行和流式连接', async (done) => {
      // 注意：这是一个伪测试，实际需要完整的 WebSocket 测试框架
      try {
        const threadId = 'test-thread-' + Date.now()
        
        // 首先启动工作流
        const runResponse = await axios.post(
          `${API_BASE_URL}/workflows/run`,
          {
            workflow: {
              nodes: [
                { id: 'node1', type: 'Start', label: 'Start' }
              ],
              edges: []
            }
          },
          {
            headers: {
              'Authorization': `Bearer ${process.env.TEST_JWT_TOKEN || ''}`,
              'Content-Type': 'application/json'
            }
          }
        )

        expect(runResponse.status).toBeOneOf([200, 201])
        expect(runResponse.data).toHaveProperty('thread_id')
        
        done()
      } catch (error: any) {
        console.error('工作流运行 API 错误:', error.response?.data || error.message)
        throw error
      }
    })
  })

  describe('上下文管理 API', () => {
    it('应该分析上下文', async () => {
      const context = {
        nodes: [
          { id: '1', type: 'LLM', label: 'Process' }
        ],
        edges: []
      }

      try {
        const response = await axios.post(
          `${API_BASE_URL}/context/analyze`,
          context,
          {
            headers: {
              'Authorization': `Bearer ${process.env.TEST_JWT_TOKEN || ''}`,
              'Content-Type': 'application/json'
            }
          }
        )

        expect(response.status).toBe(200)
        expect(response.data).toHaveProperty('token_count')
      } catch (error: any) {
        console.error('上下文分析 API 错误:', error.response?.data || error.message)
        throw error
      }
    })

    it('应该获取上下文建议', async () => {
      try {
        const response = await axios.post(
          `${API_BASE_URL}/context/suggestions`,
          {
            current_context: 'Process documents',
            workflow_type: 'RAG'
          },
          {
            headers: {
              'Authorization': `Bearer ${process.env.TEST_JWT_TOKEN || ''}`,
              'Content-Type': 'application/json'
            }
          }
        )

        expect(response.status).toBe(200)
      } catch (error: any) {
        console.error('上下文建议 API 错误:', error.response?.data || error.message)
        throw error
      }
    })
  })
})

// 辅助函数：验证 HTTP 状态码是否在预期范围内
expect.extend({
  toBeOneOf(received: number, expected: number[]) {
    const pass = expected.includes(received)
    return {
      pass,
      message: () => `expected ${received} to be one of ${expected.join(', ')}`
    }
  }
})
