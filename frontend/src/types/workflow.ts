import { Node, Edge } from 'reactflow'

export type NodeStatus = 'idle' | 'thinking' | 'executing' | 'completed' | 'error' | 'interrupted'

export interface AgentNodeData {
  label: string
  type: 'llm' | 'tool' | 'router' | 'map' | 'research' | 'writer' | 'reviewer'
  status: NodeStatus
  modelConfig?: {
    provider: 'openai' | 'anthropic'
    model: string
    temperature?: number
    maxTokens?: number
    // RAG configuration
    enableRag?: boolean
    knowledgeDocuments?: string[]
    ragMode?: 'document' | 'chunk'
    ragTopK?: number
    ragMinScore?: number
  }
  prompt?: string
  streamingContent?: string
  error?: string
  toolConfig?: {
    toolName: string
    args: Record<string, any>
  }
  // RAG search results (from WebSocket)
  ragSearchResults?: Array<{
    documentId: string
    title: string
    score: number
    snippet?: string
  }>
}

export interface CanvasViewport {
  x: number
  y: number
  zoom: number
}

export interface WorkflowCanvas {
  nodes: Node<AgentNodeData>[]
  edges: Edge[]
  viewport: CanvasViewport
}

export interface Workflow {
  id: string
  ownerId: string
  title: string
  description: string
  canvasJson: WorkflowCanvas
  sourceTemplateId?: string
  isPublic: boolean
  createdAt: string
  updatedAt: string
}

export interface WorkflowRun {
  id: string
  workflowId: string
  threadId: string
  status: 'running' | 'completed' | 'failed' | 'interrupted'
  inputSummary: string
  startedAt: string
  finishedAt?: string
}

export interface WorkflowCreateInput {
  title: string
  description: string
  canvasJson?: WorkflowCanvas
  sourceTemplateId?: string
}

export interface WorkflowUpdateInput {
  title?: string
  description?: string
  canvasJson?: WorkflowCanvas
  isPublic?: boolean
}
