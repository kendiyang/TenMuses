/**
 * useWorkflowContext Hook
 *
 * 获取当前工作流的上下文信息，包括节点、边等
 */

import { useCallback } from 'react'
import { useWorkflowStore } from '@/stores/workflow-store'

export interface WorkflowContextType {
  nodes: any[]
  edges: any[]
  description?: string
  nodeCount: number
  edgeCount: number
}

/**
 * 获取当前工作流的上下文信息
 */
export function useWorkflowContext() {
  const { nodes, edges } = useWorkflowStore()

  const getContext = useCallback((): WorkflowContextType => {
    return {
      nodes: nodes.map((node) => ({
        id: node.id,
        type: node.data?.type || 'unknown',
        label: node.data?.label,
        config: node.data?.modelConfig || {},
        description: node.data?.prompt,
        position: node.position,
      })),
      edges: edges.map((edge) => ({
        id: edge.id,
        source: edge.source,
        target: edge.target,
        sourceHandle: edge.sourceHandle,
        targetHandle: edge.targetHandle,
      })),
      nodeCount: nodes.length,
      edgeCount: edges.length,
    }
  }, [nodes, edges])

  /**
   * 获取格式化的工作流描述
   */
  const getFormattedWorkflow = useCallback(() => {
    const context = getContext()

    const nodesList = context.nodes
      .map((n) => `- ${n.label || n.type} (${n.type})`)
      .join('\n')

    const edgesList = context.edges
      .map((e) => `- ${context.nodes.find((n) => n.id === e.source)?.label || e.source} -> ${context.nodes.find((n) => n.id === e.target)?.label || e.target}`)
      .join('\n')

    return `
工作流概览:
- 节点数: ${context.nodeCount}
- 连接数: ${context.edgeCount}

节点列表:
${nodesList || '(无节点)'}

连接列表:
${edgesList || '(无连接)'}
    `.trim()
  }, [getContext])

  return {
    getContext,
    getFormattedWorkflow,
  }
}
