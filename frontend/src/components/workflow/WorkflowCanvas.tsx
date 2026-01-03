'use client'

import { useCallback } from 'react'
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  Connection,
  Edge,
  addEdge,
  ConnectionMode,
} from 'reactflow'
import 'reactflow/dist/style.css'
import { useWorkflowStore } from '@/stores/workflow-store'
import AgentNode from './AgentNode'

const nodeTypes = {
  agent: AgentNode,
}

interface WorkflowCanvasProps {
  onNodeSelect: (nodeId: string | null) => void
}

export default function WorkflowCanvas({ onNodeSelect }: WorkflowCanvasProps) {
  const { nodes, edges, onNodesChange, onEdgesChange, addEdge: addEdgeToStore } = useWorkflowStore()

  const onConnect = useCallback(
    (connection: Connection) => {
      const edge: Edge = {
        id: `${connection.source}-${connection.target}`,
        source: connection.source!,
        target: connection.target!,
        sourceHandle: connection.sourceHandle,
        targetHandle: connection.targetHandle,
      }
      addEdgeToStore(edge)
    },
    [addEdgeToStore]
  )

  const onNodeClick = useCallback(
    (_event: React.MouseEvent, node: any) => {
      onNodeSelect(node.id)
    },
    [onNodeSelect]
  )

  const onPaneClick = useCallback(() => {
    onNodeSelect(null)
  }, [onNodeSelect])

  return (
    <ReactFlow
      nodes={nodes}
      edges={edges}
      onNodesChange={onNodesChange}
      onEdgesChange={onEdgesChange}
      onConnect={onConnect}
      onNodeClick={onNodeClick}
      onPaneClick={onPaneClick}
      nodeTypes={nodeTypes}
      connectionMode={ConnectionMode.Loose}
      fitView
      className="bg-background"
    >
      <Background />
      <Controls />
      <MiniMap
        nodeColor={(node) => {
          switch (node.data.status) {
            case 'completed':
              return '#22c55e'
            case 'executing':
              return '#3b82f6'
            case 'error':
              return '#ef4444'
            default:
              return '#94a3b8'
          }
        }}
      />
    </ReactFlow>
  )
}
