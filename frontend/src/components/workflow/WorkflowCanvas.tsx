'use client'

import { useCallback, useState } from 'react'
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
import NodeSelectorPanel from './NodeSelectorPanel'
import { Plus, Search, Copy, Maximize2 } from 'lucide-react'

const nodeTypes = {
  agent: AgentNode,
}

interface WorkflowCanvasProps {
  onNodeSelect: (nodeId: string | null) => void
}

export default function WorkflowCanvas({ onNodeSelect }: WorkflowCanvasProps) {
  const { nodes, edges, onNodesChange, onEdgesChange, addEdge: addEdgeToStore, addNode } = useWorkflowStore()
  const [showNodeSelector, setShowNodeSelector] = useState(false)
  const [selectorPosition, setSelectorPosition] = useState<{ x: number; y: number } | undefined>()

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

  const handleShowNodeSelector = useCallback((position?: { x: number; y: number }) => {
    setSelectorPosition(position)
    setShowNodeSelector(true)
  }, [])

  const handleAddNode = useCallback((nodeType: any, nodeId: string) => {
    const newNodeId = `node-${Date.now()}`
    addNode({
      id: newNodeId,
      type: 'agent',
      position: { x: 250, y: 250 },
      data: {
        label: nodeId.replace(/-/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase()),
        type: nodeType,
        status: 'idle',
      },
    })
    onNodeSelect(newNodeId)
  }, [addNode, onNodeSelect])

  return (
    <div className="relative w-full h-full">
      {/* Empty State - Add First Step */}
      {nodes.length === 0 && (
        <div className="absolute inset-0 flex flex-col items-center justify-center z-10 pointer-events-none">
          <div
            className="border-2 border-gray-300 rounded-lg p-12 bg-white/50 text-center pointer-events-auto cursor-pointer hover:bg-white/70 transition-colors"
            onClick={() => handleShowNodeSelector()}
          >
            <div className="w-16 h-16 mx-auto mb-4 border-2 border-dashed border-gray-400 rounded-lg flex items-center justify-center">
              <Plus className="w-8 h-8 text-gray-400" />
            </div>
            <p className="text-gray-700 font-medium mb-1">Add first step...</p>
            <p className="text-red-500 text-sm">or start from a template</p>
          </div>
        </div>
      )}

      {/* Right Side Floating Toolbar */}
      <div className="absolute right-4 top-4 z-20 flex flex-col gap-2 border border-gray-300 rounded-lg bg-white p-2 shadow-lg">
        <button
          onClick={() => handleShowNodeSelector({ x: 0, y: 100 })}
          className="p-2 hover:bg-gray-100 rounded transition-colors"
          title="Add node"
        >
          <Plus className="w-5 h-5 text-gray-600" />
        </button>
        <button
          className="p-2 hover:bg-gray-100 rounded transition-colors"
          title="Search nodes"
        >
          <Search className="w-5 h-5 text-gray-600" />
        </button>
        <button
          className="p-2 hover:bg-gray-100 rounded transition-colors"
          title="Duplicate"
        >
          <Copy className="w-5 h-5 text-gray-600" />
        </button>
        <button
          className="p-2 hover:bg-gray-100 rounded transition-colors"
          title="Fullscreen"
        >
          <Maximize2 className="w-5 h-5 text-gray-600" />
        </button>
      </div>

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

      {/* Node Selector Panel */}
      {showNodeSelector && (
        <NodeSelectorPanel
          onClose={() => setShowNodeSelector(false)}
          onSelectNode={handleAddNode}
          position={selectorPosition}
        />
      )}
    </div>
  )
}

