/**
 * Copilot Types
 */

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  timestamp: number
  suggestions?: any
  diagnostics?: any
  template?: LLMPromptTemplate
}

export interface NodeConfig {
  type: string
  label?: string
  config?: Record<string, any>
}

export interface Edge {
  from: string
  to: string
}

export interface WorkflowSuggestion {
  name: string
  description: string
  nodes: NodeConfig[]
  edges: Edge[]
  explanation: string
}

export interface NodeSuggestion {
  type: string
  label?: string
  config?: Record<string, any>
  explanation: string
}

export interface Diagnostic {
  level: 'error' | 'warning' | 'info'
  type: string
  description: string
  location?: Record<string, any>
  suggestion: string
}

export interface WorkflowDiagnosis {
  diagnostics: Diagnostic[]
  score: number
  summary: string
}

export interface LLMPromptTemplate {
  content: string
  version: string
  description?: string
  examples?: string[]
}

export interface PromptTemplate {
  prompt: string
  style: 'structured' | 'detailed' | 'concise'
  estimated_tokens: number
}

// API Request/Response Types

export interface ChatRequest {
  message: string
  chat_history?: Array<{ role: 'user' | 'assistant'; content: string }>
  context?: Record<string, any>
  model?: string // AI模型选择: local-smart | local-rules | gpt-4 | claude-3
}

export interface ChatResponse {
  message: string
  suggestions?: any
  diagnostics?: any
}

export interface WorkflowSuggestionRequest {
  description: string
  complexity?: 'simple' | 'medium' | 'advanced'
  model?: string // AI模型选择: local-smart | local-rules | gpt-4 | claude-3
}

export interface WorkflowSuggestionResponse {
  workflows: WorkflowSuggestion[]
}

export interface NodeSuggestionRequest {
  context: string
  previous_node_type?: string
  workflow_description?: string
  model?: string // AI模型选择: local-smart | local-rules | gpt-4 | claude-3
}

export interface NodeSuggestionResponse {
  suggestions: NodeSuggestion[]
}

export interface WorkflowDiagnosisRequest {
  nodes: any[]
  edges: any[]
  model?: string // AI模型选择: local-smart | local-rules | gpt-4 | claude-3
}

export interface WorkflowDiagnosisResponse {
  diagnostics: Diagnostic[]
  score: number
  summary: string
}

export interface PromptGenerationRequest {
  task_description: string
  input_format?: string
  output_format?: string
  examples?: Array<{ input: string; output: string }>
  style?: 'structured' | 'detailed' | 'concise'
  model?: string // AI模型选择: local-smart | local-rules | gpt-4 | claude-3
}

export interface PromptGenerationResponse {
  template: PromptTemplate
}
