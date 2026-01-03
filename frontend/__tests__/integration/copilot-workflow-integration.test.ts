/**
 * Copilot 工作流集成测试
 * 
 * 测试 Copilot 面板与工作流编辑器的集成
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useWorkflowContext } from '@/hooks/useWorkflowContext'
import { useWorkflowStore } from '@/stores/workflow-store'

describe('Copilot Workflow Integration', () => {
  beforeEach(() => {
    // 重置 store
    const store = useWorkflowStore.getState()
    store.reset()
  })

  describe('useWorkflowContext Hook', () => {
    it('应该返回空的工作流上下文', () => {
      const { result } = renderHook(() => useWorkflowContext())

      const context = result.current.getContext()

      expect(context.nodes).toEqual([])
      expect(context.edges).toEqual([])
      expect(context.nodeCount).toBe(0)
      expect(context.edgeCount).toBe(0)
    })

    it('应该返回正确的工作流上下文', () => {
      const { result: storeResult } = renderHook(() => useWorkflowStore())
      const { result: contextResult } = renderHook(() => useWorkflowContext())

      // 添加节点
      act(() => {
        storeResult.current.addNode({
          id: 'node-1',
          data: {
            label: 'Test Node',
            type: 'llm',
            config: { model: 'gpt-4' },
            description: 'A test node',
          },
          position: { x: 0, y: 0 },
          type: 'agent',
        })
      })

      // 添加节点
      act(() => {
        storeResult.current.addNode({
          id: 'node-2',
          data: {
            label: 'Another Node',
            type: 'tool',
            config: {},
            description: 'Another test node',
          },
          position: { x: 100, y: 0 },
          type: 'agent',
        })
      })

      // 添加边
      act(() => {
        storeResult.current.addEdge({
          id: 'edge-1',
          source: 'node-1',
          target: 'node-2',
          sourceHandle: undefined,
          targetHandle: undefined,
        })
      })

      const context = contextResult.current.getContext()

      expect(context.nodeCount).toBe(2)
      expect(context.edgeCount).toBe(1)
      expect(context.nodes).toHaveLength(2)
      expect(context.edges).toHaveLength(1)

      // 检查节点数据
      expect(context.nodes[0]).toEqual({
        id: 'node-1',
        type: 'llm',
        label: 'Test Node',
        config: { model: 'gpt-4' },
        description: 'A test node',
        position: { x: 0, y: 0 },
      })

      // 检查边数据
      expect(context.edges[0]).toEqual({
        id: 'edge-1',
        source: 'node-1',
        target: 'node-2',
        sourceHandle: undefined,
        targetHandle: undefined,
      })
    })

    it('应该生成格式化的工作流描述', () => {
      const { result: storeResult } = renderHook(() => useWorkflowStore())
      const { result: contextResult } = renderHook(() => useWorkflowContext())

      // 添加节点
      act(() => {
        storeResult.current.addNode({
          id: 'node-1',
          data: {
            label: 'Research',
            type: 'llm',
            config: {},
            description: '',
          },
          position: { x: 0, y: 0 },
          type: 'agent',
        })

        storeResult.current.addNode({
          id: 'node-2',
          data: {
            label: 'Write',
            type: 'llm',
            config: {},
            description: '',
          },
          position: { x: 100, y: 0 },
          type: 'agent',
        })

        storeResult.current.addEdge({
          id: 'edge-1',
          source: 'node-1',
          target: 'node-2',
          sourceHandle: undefined,
          targetHandle: undefined,
        })
      })

      const formatted = contextResult.current.getFormattedWorkflow()

      expect(formatted).toContain('工作流概览')
      expect(formatted).toContain('节点数: 2')
      expect(formatted).toContain('连接数: 1')
      expect(formatted).toContain('Research')
      expect(formatted).toContain('Write')
    })
  })

  describe('Node Suggestion Application', () => {
    it('应该正确应用节点建议', () => {
      const { result: storeResult } = renderHook(() => useWorkflowStore())

      const nodeSuggestion = {
        type: 'llm',
        label: 'Suggested Node',
        config: { model: 'gpt-4' },
        description: 'A suggested node',
      }

      // 模拟添加节点
      act(() => {
        const nodeId = `node_${Date.now()}_test`
        storeResult.current.addNode({
          id: nodeId,
          data: {
            label: nodeSuggestion.label,
            type: nodeSuggestion.type,
            config: nodeSuggestion.config,
            description: nodeSuggestion.description,
            status: 'idle',
          },
          position: { x: 250, y: 250 },
          type: 'agent',
        })
      })

      const nodes = storeResult.current.nodes

      expect(nodes).toHaveLength(1)
      expect(nodes[0].data.label).toBe('Suggested Node')
      expect(nodes[0].data.type).toBe('llm')
    })

    it('应该正确应用工作流建议', () => {
      const { result: storeResult } = renderHook(() => useWorkflowStore())

      const workflowSuggestion = {
        name: 'Research & Write Workflow',
        description: 'A workflow for researching and writing',
        nodes: [
          {
            id: 'research',
            type: 'llm',
            label: 'Research Node',
            config: { model: 'gpt-4' },
          },
          {
            id: 'write',
            type: 'llm',
            label: 'Write Node',
            config: { model: 'gpt-4' },
          },
        ],
        edges: [
          {
            source: 'research',
            target: 'write',
          },
        ],
      }

      // 应用工作流
      act(() => {
        const newNodes = workflowSuggestion.nodes.map((node, idx) => ({
          id: node.id,
          data: {
            label: node.label,
            type: node.type,
            config: node.config,
            description: '',
            status: 'idle' as const,
          },
          position: {
            x: (idx % 3) * 300 + 50,
            y: Math.floor(idx / 3) * 150 + 50,
          },
          type: 'agent',
        }))

        const newEdges = workflowSuggestion.edges.map((edge) => ({
          id: `${edge.source}-${edge.target}`,
          source: edge.source,
          target: edge.target,
          sourceHandle: undefined,
          targetHandle: undefined,
        }))

        storeResult.current.setNodes(newNodes)
        storeResult.current.setEdges(newEdges)
      })

      expect(storeResult.current.nodes).toHaveLength(2)
      expect(storeResult.current.edges).toHaveLength(1)
    })
  })

  describe('Context Passing', () => {
    it('应该在发送消息时包含工作流上下文', () => {
      const { result: storeResult } = renderHook(() => useWorkflowStore())
      const { result: contextResult } = renderHook(() => useWorkflowContext())

      // 添加节点
      act(() => {
        storeResult.current.addNode({
          id: 'node-1',
          data: {
            label: 'Test',
            type: 'llm',
            config: {},
            description: '',
            status: 'idle',
          },
          position: { x: 0, y: 0 },
          type: 'agent',
        })
      })

      const context = contextResult.current.getContext()

      // 验证上下文包含工作流信息
      expect(context).toHaveProperty('nodes')
      expect(context).toHaveProperty('edges')
      expect(context).toHaveProperty('nodeCount')
      expect(context).toHaveProperty('edgeCount')
      expect(context.nodeCount).toBe(1)
      expect(context.nodes[0].type).toBe('llm')
    })
  })

  describe('Error Handling', () => {
    it('应该处理空工作流上下文', () => {
      const { result } = renderHook(() => useWorkflowContext())

      const context = result.current.getContext()
      const formatted = result.current.getFormattedWorkflow()

      expect(context.nodeCount).toBe(0)
      expect(context.edgeCount).toBe(0)
      expect(formatted).toContain('(无节点)')
      expect(formatted).toContain('(无连接)')
    })

    it('应该处理部分上下文信息', () => {
      const { result: storeResult } = renderHook(() => useWorkflowStore())
      const { result: contextResult } = renderHook(() => useWorkflowContext())

      // 添加只有节点，没有边的情况
      act(() => {
        storeResult.current.addNode({
          id: 'node-1',
          data: {
            label: 'Test',
            type: 'llm',
            config: {},
            description: '',
            status: 'idle',
          },
          position: { x: 0, y: 0 },
          type: 'agent',
        })
      })

      const context = contextResult.current.getContext()
      const formatted = contextResult.current.getFormattedWorkflow()

      expect(context.nodeCount).toBe(1)
      expect(context.edgeCount).toBe(0)
      expect(formatted).toContain('(无连接)')
      expect(formatted).toContain('Test')
    })
  })
})
