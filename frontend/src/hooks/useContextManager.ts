/**
 * useContextManager Hook
 * 
 * React hook for managing workflow context state
 */

'use client'

import { useState, useMemo, useCallback } from 'react'
import { Node, Edge } from 'reactflow'
import {
  ContextItem,
  ContextConfig,
  ContextAnalysis,
  ContextManager
} from '@/lib/context-manager'

export interface UseContextManagerOptions {
  nodes: Node[]
  edges: Edge[]
  metadata?: Record<string, any>
  initialConfig?: Partial<ContextConfig>
}

export function useContextManager({
  nodes,
  edges,
  metadata,
  initialConfig
}: UseContextManagerOptions) {
  // Initialize config
  const [config, setConfig] = useState<ContextConfig>(() => ({
    ...ContextManager.getDefaultConfig(),
    ...initialConfig
  }))

  // Create context items from workflow data
  const baseItems = useMemo(() => {
    return ContextManager.createContextItems(nodes, edges, metadata)
  }, [nodes, edges, metadata])

  // Apply configuration to items
  const items = useMemo(() => {
    return ContextManager.applyConfig(baseItems, config)
  }, [baseItems, config])

  // Analyze context
  const analysis = useMemo(() => {
    return ContextManager.analyze(items, config)
  }, [items, config])

  // Update configuration
  const updateConfig = useCallback((updates: Partial<ContextConfig>) => {
    setConfig(prev => ({ ...prev, ...updates }))
  }, [])

  // Toggle individual item
  const toggleItem = useCallback((itemId: string) => {
    setConfig(prev => {
      const item = baseItems.find(i => i.id === itemId)
      if (!item) return prev

      const newConfig = { ...prev }

      if (item.type === 'metadata') {
        newConfig.includeWorkflowMetadata = !prev.includeWorkflowMetadata
      } else if (item.type === 'node') {
        const nodeId = item.content.id
        const isSelected = prev.selectedNodeIds.includes(nodeId)
        
        if (isSelected) {
          newConfig.selectedNodeIds = prev.selectedNodeIds.filter(id => id !== nodeId)
        } else {
          newConfig.selectedNodeIds = [...prev.selectedNodeIds, nodeId]
        }

        // If all nodes are deselected, set includeNodes to false
        if (newConfig.selectedNodeIds.length === 0) {
          newConfig.includeNodes = false
        } else {
          newConfig.includeNodes = true
        }
      } else if (item.type === 'edge') {
        newConfig.includeEdges = !prev.includeEdges
      }

      return newConfig
    })
  }, [baseItems])

  // Select all items
  const selectAll = useCallback(() => {
    setConfig({
      ...config,
      includeWorkflowMetadata: true,
      includeNodes: true,
      includeEdges: true,
      selectedNodeIds: baseItems
        .filter(item => item.type === 'node')
        .map(item => item.content.id)
    })
  }, [config, baseItems])

  // Deselect all items
  const deselectAll = useCallback(() => {
    setConfig({
      ...config,
      includeWorkflowMetadata: false,
      includeNodes: false,
      includeEdges: false,
      selectedNodeIds: []
    })
  }, [config])

  // Optimize for token limit
  const optimizeForLimit = useCallback((maxTokens: number) => {
    const optimized = ContextManager.optimizeForTokenLimit(baseItems, maxTokens)
    
    const selectedNodeIds = optimized
      .filter(item => item.type === 'node' && item.selected)
      .map(item => item.content.id)
    
    setConfig({
      ...config,
      maxTokens,
      includeWorkflowMetadata: optimized.some(item => item.type === 'metadata' && item.selected),
      includeNodes: optimized.some(item => item.type === 'node' && item.selected),
      includeEdges: optimized.some(item => item.type === 'edge' && item.selected),
      selectedNodeIds
    })
  }, [config, baseItems])

  // Serialize context for API
  const serialize = useCallback(() => {
    return ContextManager.serializeContext(items)
  }, [items])

  // Get summary text
  const summary = useMemo(() => {
    return ContextManager.getSummary(items)
  }, [items])

  return {
    items,
    config,
    analysis,
    summary,
    updateConfig,
    toggleItem,
    selectAll,
    deselectAll,
    optimizeForLimit,
    serialize
  }
}
