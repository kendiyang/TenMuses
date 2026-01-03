/**
 * Context Manager for Copilot
 * 
 * Manages workflow and node context for AI interactions:
 * - Context selection and filtering
 * - Token counting and size estimation
 * - Context optimization suggestions
 * - Context serialization
 */

import { Node, Edge } from 'reactflow'

/**
 * Context item types
 */
export type ContextItemType = 'workflow' | 'node' | 'edge' | 'metadata'

/**
 * Context item representing a piece of workflow information
 */
export interface ContextItem {
  id: string
  type: ContextItemType
  label: string
  content: any
  size: number  // estimated size in characters
  tokens: number  // estimated token count
  importance: 'high' | 'medium' | 'low'
  selected: boolean
}

/**
 * Context configuration
 */
export interface ContextConfig {
  includeWorkflowMetadata: boolean
  includeNodes: boolean
  includeEdges: boolean
  selectedNodeIds: string[]
  maxTokens?: number
  prioritizeRecent: boolean
}

/**
 * Context analysis result
 */
export interface ContextAnalysis {
  totalItems: number
  totalSize: number
  totalTokens: number
  selectedItems: number
  selectedSize: number
  selectedTokens: number
  suggestions: ContextSuggestion[]
  warnings: ContextWarning[]
}

/**
 * Context optimization suggestion
 */
export interface ContextSuggestion {
  id: string
  type: 'reduce' | 'add' | 'prioritize' | 'remove'
  severity: 'info' | 'warning' | 'error'
  title: string
  description: string
  impact?: {
    tokensSaved?: number
    tokensAdded?: number
  }
  action?: () => void
}

/**
 * Context warning
 */
export interface ContextWarning {
  id: string
  type: 'too_large' | 'missing_info' | 'redundant' | 'deprecated'
  message: string
  affectedItems: string[]
}

/**
 * Context Manager Class
 */
export class ContextManager {
  /**
   * Estimate token count from text (rough approximation: 1 token ≈ 4 characters)
   */
  static estimateTokens(text: string): number {
    return Math.ceil(text.length / 4)
  }

  /**
   * Estimate size of an object in characters
   */
  static estimateSize(obj: any): number {
    return JSON.stringify(obj).length
  }

  /**
   * Create context items from workflow data
   */
  static createContextItems(
    nodes: Node[],
    edges: Edge[],
    metadata?: Record<string, any>
  ): ContextItem[] {
    const items: ContextItem[] = []

    // Workflow metadata
    if (metadata) {
      const content = metadata
      const size = this.estimateSize(content)
      items.push({
        id: 'workflow-metadata',
        type: 'metadata',
        label: 'Workflow Metadata',
        content,
        size,
        tokens: this.estimateTokens(JSON.stringify(content)),
        importance: 'high',
        selected: true
      })
    }

    // Nodes
    nodes.forEach(node => {
      const content = {
        id: node.id,
        type: node.type,
        data: node.data,
        position: node.position
      }
      const size = this.estimateSize(content)
      items.push({
        id: `node-${node.id}`,
        type: 'node',
        label: node.data?.label || node.id,
        content,
        size,
        tokens: this.estimateTokens(JSON.stringify(content)),
        importance: this.determineNodeImportance(node),
        selected: true
      })
    })

    // Edges
    edges.forEach(edge => {
      const content = {
        id: edge.id,
        source: edge.source,
        target: edge.target,
        sourceHandle: edge.sourceHandle,
        targetHandle: edge.targetHandle
      }
      const size = this.estimateSize(content)
      items.push({
        id: `edge-${edge.id}`,
        type: 'edge',
        label: `${edge.source} → ${edge.target}`,
        content,
        size,
        tokens: this.estimateTokens(JSON.stringify(content)),
        importance: 'low',
        selected: false  // Edges are less important by default
      })
    })

    return items
  }

  /**
   * Determine importance of a node based on its type and properties
   */
  private static determineNodeImportance(node: Node): 'high' | 'medium' | 'low' {
    const type = node.type?.toLowerCase() || ''
    
    // High importance nodes
    if (type.includes('llm') || type.includes('agent') || type.includes('rag')) {
      return 'high'
    }
    
    // Medium importance nodes
    if (type.includes('retriever') || type.includes('vector') || type.includes('search')) {
      return 'medium'
    }
    
    // Low importance nodes
    return 'low'
  }

  /**
   * Apply context configuration to items
   */
  static applyConfig(items: ContextItem[], config: ContextConfig): ContextItem[] {
    return items.map(item => {
      let selected = item.selected

      // Apply type filters
      if (item.type === 'metadata' && !config.includeWorkflowMetadata) {
        selected = false
      }
      if (item.type === 'node' && !config.includeNodes) {
        selected = false
      }
      if (item.type === 'edge' && !config.includeEdges) {
        selected = false
      }

      // Apply node selection
      if (item.type === 'node' && config.selectedNodeIds.length > 0) {
        const nodeId = item.content.id
        selected = config.selectedNodeIds.includes(nodeId)
      }

      return { ...item, selected }
    })
  }

  /**
   * Analyze context and provide insights
   */
  static analyze(items: ContextItem[], config?: ContextConfig): ContextAnalysis {
    const selectedItems = items.filter(item => item.selected)
    
    const totalSize = items.reduce((sum, item) => sum + item.size, 0)
    const totalTokens = items.reduce((sum, item) => sum + item.tokens, 0)
    
    const selectedSize = selectedItems.reduce((sum, item) => sum + item.size, 0)
    const selectedTokens = selectedItems.reduce((sum, item) => sum + item.tokens, 0)

    const suggestions: ContextSuggestion[] = []
    const warnings: ContextWarning[] = []

    // Check if context is too large
    const maxTokens = config?.maxTokens || 8000
    if (selectedTokens > maxTokens) {
      warnings.push({
        id: 'context-too-large',
        type: 'too_large',
        message: `Context exceeds ${maxTokens} tokens (current: ${selectedTokens})`,
        affectedItems: selectedItems.map(item => item.id)
      })

      suggestions.push({
        id: 'reduce-context',
        type: 'reduce',
        severity: 'error',
        title: 'Context Too Large',
        description: `Reduce context by ${selectedTokens - maxTokens} tokens`,
        impact: {
          tokensSaved: selectedTokens - maxTokens
        }
      })
    }

    // Suggest including edges if only nodes are selected
    const hasNodes = selectedItems.some(item => item.type === 'node')
    const hasEdges = selectedItems.some(item => item.type === 'edge')
    if (hasNodes && !hasEdges) {
      suggestions.push({
        id: 'include-edges',
        type: 'add',
        severity: 'info',
        title: 'Consider Including Edges',
        description: 'Adding edge information can help understand workflow structure',
        impact: {
          tokensAdded: items.filter(item => item.type === 'edge').reduce((sum, item) => sum + item.tokens, 0)
        }
      })
    }

    // Suggest including metadata if missing
    const hasMetadata = selectedItems.some(item => item.type === 'metadata')
    if (!hasMetadata) {
      suggestions.push({
        id: 'include-metadata',
        type: 'add',
        severity: 'warning',
        title: 'Workflow Metadata Missing',
        description: 'Including workflow metadata provides important context',
        impact: {
          tokensAdded: items.filter(item => item.type === 'metadata').reduce((sum, item) => sum + item.tokens, 0)
        }
      })
    }

    // Check for redundant node selection
    if (selectedItems.length === items.length && items.length > 10) {
      suggestions.push({
        id: 'reduce-nodes',
        type: 'prioritize',
        severity: 'info',
        title: 'Consider Selecting Specific Nodes',
        description: 'Selecting only relevant nodes can improve AI response quality',
        impact: {
          tokensSaved: Math.floor(selectedTokens * 0.5)
        }
      })
    }

    return {
      totalItems: items.length,
      totalSize,
      totalTokens,
      selectedItems: selectedItems.length,
      selectedSize,
      selectedTokens,
      suggestions,
      warnings
    }
  }

  /**
   * Serialize selected context for API
   */
  static serializeContext(items: ContextItem[]): any {
    const selectedItems = items.filter(item => item.selected)
    
    const context: any = {
      nodes: [],
      edges: [],
      metadata: {}
    }

    selectedItems.forEach(item => {
      if (item.type === 'node') {
        context.nodes.push(item.content)
      } else if (item.type === 'edge') {
        context.edges.push(item.content)
      } else if (item.type === 'metadata') {
        context.metadata = { ...context.metadata, ...item.content }
      }
    })

    return context
  }

  /**
   * Get default context configuration
   */
  static getDefaultConfig(): ContextConfig {
    return {
      includeWorkflowMetadata: true,
      includeNodes: true,
      includeEdges: false,
      selectedNodeIds: [],
      maxTokens: 8000,
      prioritizeRecent: false
    }
  }

  /**
   * Optimize context based on token limit
   */
  static optimizeForTokenLimit(
    items: ContextItem[],
    maxTokens: number
  ): ContextItem[] {
    // Sort by importance: high > medium > low
    const sorted = [...items].sort((a, b) => {
      const importanceOrder = { high: 3, medium: 2, low: 1 }
      return importanceOrder[b.importance] - importanceOrder[a.importance]
    })

    let currentTokens = 0
    const optimized = sorted.map(item => {
      if (currentTokens + item.tokens <= maxTokens) {
        currentTokens += item.tokens
        return { ...item, selected: true }
      }
      return { ...item, selected: false }
    })

    return optimized
  }

  /**
   * Get context summary text
   */
  static getSummary(items: ContextItem[]): string {
    const selected = items.filter(item => item.selected)
    const nodeCount = selected.filter(item => item.type === 'node').length
    const edgeCount = selected.filter(item => item.type === 'edge').length
    const hasMetadata = selected.some(item => item.type === 'metadata')

    const parts = []
    if (hasMetadata) parts.push('workflow metadata')
    if (nodeCount > 0) parts.push(`${nodeCount} node${nodeCount > 1 ? 's' : ''}`)
    if (edgeCount > 0) parts.push(`${edgeCount} edge${edgeCount > 1 ? 's' : ''}`)

    return parts.join(', ') || 'No context selected'
  }
}

/**
 * Hook for managing context state (for React components)
 */
export interface UseContextManagerResult {
  items: ContextItem[]
  config: ContextConfig
  analysis: ContextAnalysis
  updateConfig: (config: Partial<ContextConfig>) => void
  toggleItem: (itemId: string) => void
  selectAll: () => void
  deselectAll: () => void
  optimizeForLimit: (maxTokens: number) => void
  serialize: () => any
}
