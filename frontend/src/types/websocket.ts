export type WSEventType =
  | 'connected'
  | 'run_started'
  | 'run_completed'
  | 'run_failed'
  | 'node_started'
  | 'node_status'
  | 'node_completed'
  | 'token'
  | 'tool_call'
  | 'error'
  | 'interrupt'
  | 'rag_search_started'
  | 'rag_result'
  | 'rag_error'
  | 'rag_complete'

export interface WSEvent<T = any> {
  type: WSEventType
  runId: string
  threadId: string
  nodeId?: string
  payload: T
}

export interface RunStartedPayload {
  workflowId: string
  inputSummary: string
}

export interface RunCompletedPayload {
  status: 'completed' | 'failed'
  durationMs: number
}

export interface NodeStatusPayload {
  status: 'idle' | 'thinking' | 'executing' | 'completed' | 'error' | 'interrupted'
}

export interface TokenPayload {
  content: string
  sequence: number
  finished: boolean
}

export interface ToolCallPayload {
  tool: string
  args: Record<string, any>
  componentHint?: string
}

export interface ErrorPayload {
  message: string
  code: string
  fatal: boolean
}

export interface InterruptPayload {
  inputState: Record<string, any>
  reason: string
}

// RAG 事件有效负载类型定义
export interface RagSearchStartedPayload {
  query: string
  topK: number
  minScore: number
  ragMode: 'document' | 'chunk'
  documentsCount: number
}

export interface RagResult {
  id: string
  title?: string
  content: string
  score: number
  metadata?: Record<string, any>
  chunkIndex?: number
}

export interface RagResultPayload {
  results: RagResult[]
  query: string
  totalCount: number
  durationMs: number
}

export interface RagErrorPayload {
  message: string
  code: string
  nodeId?: string
}

export interface RagCompletePayload {
  status: 'success' | 'failed'
  totalResults: number
  durationMs: number
}
