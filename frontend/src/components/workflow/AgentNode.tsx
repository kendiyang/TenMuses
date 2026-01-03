'use client'

import { memo } from 'react'
import { Handle, Position, NodeProps } from 'reactflow'
import { AgentNodeData } from '@/types/workflow'
import { Brain, FileText, CheckCircle, Loader2, AlertCircle } from 'lucide-react'

const nodeIcons = {
  research: Brain,
  writer: FileText,
  reviewer: CheckCircle,
  llm: Brain,
  tool: FileText,
  router: CheckCircle,
  map: Brain,
}

const statusColors = {
  idle: 'border-gray-300 bg-white',
  thinking: 'border-blue-400 bg-blue-50',
  executing: 'border-blue-500 bg-blue-100',
  completed: 'border-green-500 bg-green-50',
  error: 'border-red-500 bg-red-50',
  interrupted: 'border-yellow-500 bg-yellow-50',
}

function AgentNode({ data, selected }: NodeProps<AgentNodeData>) {
  const Icon = nodeIcons[data.type] || Brain
  const colorClass = statusColors[data.status] || statusColors.idle

  return (
    <div
      className={`px-4 py-3 rounded-lg border-2 shadow-md min-w-[200px] ${colorClass} ${
        selected ? 'ring-2 ring-primary' : ''
      }`}
    >
      <Handle type="target" position={Position.Left} className="w-3 h-3" />
      
      <div className="flex items-center gap-2 mb-2">
        <Icon className="w-5 h-5" />
        <div className="font-semibold text-sm">{data.label}</div>
      </div>

      <div className="text-xs text-muted-foreground mb-2">
        {data.type.charAt(0).toUpperCase() + data.type.slice(1)}
      </div>

      {/* Status indicator */}
      <div className="flex items-center gap-2 text-xs">
        {data.status === 'executing' && (
          <>
            <Loader2 className="w-3 h-3 animate-spin" />
            <span>Executing...</span>
          </>
        )}
        {data.status === 'completed' && (
          <>
            <CheckCircle className="w-3 h-3 text-green-600" />
            <span>Completed</span>
          </>
        )}
        {data.status === 'error' && (
          <>
            <AlertCircle className="w-3 h-3 text-red-600" />
            <span>Error</span>
          </>
        )}
        {data.status === 'idle' && <span className="text-muted-foreground">Ready</span>}
      </div>

      {/* Streaming content preview */}
      {data.streamingContent && (
        <div className="mt-2 p-2 bg-background rounded text-xs max-h-20 overflow-hidden">
          {data.streamingContent.slice(0, 100)}
          {data.streamingContent.length > 100 && '...'}
        </div>
      )}

      {/* Error message */}
      {data.error && (
        <div className="mt-2 p-2 bg-red-100 rounded text-xs text-red-700">
          {data.error}
        </div>
      )}

      <Handle type="source" position={Position.Right} className="w-3 h-3" />
    </div>
  )
}

export default memo(AgentNode)
