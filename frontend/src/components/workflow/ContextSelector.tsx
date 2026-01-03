/**
 * ContextSelector Component
 * 
 * Visual interface for selecting and configuring workflow context:
 * - Node/Edge/Metadata selection
 * - Importance-based filtering
 * - Quick actions (Select All, Optimize, etc.)
 */

'use client'

import React, { useState, useMemo } from 'react'
import { 
  ContextItem, 
  ContextConfig, 
  ContextManager 
} from '@/lib/context-manager'
import { 
  CheckSquare, 
  Square, 
  AlertCircle, 
  TrendingUp, 
  Minimize2,
  Filter,
  CheckCircle
} from 'lucide-react'
import { cn } from '@/lib/utils'

export interface ContextSelectorProps {
  items: ContextItem[]
  config: ContextConfig
  onConfigChange: (config: ContextConfig) => void
  onItemToggle: (itemId: string) => void
  className?: string
}

export function ContextSelector({
  items,
  config,
  onConfigChange,
  onItemToggle,
  className
}: ContextSelectorProps) {
  const [filterImportance, setFilterImportance] = useState<'all' | 'high' | 'medium' | 'low'>('all')

  // Filter items by type and importance
  const filteredItems = useMemo(() => {
    let filtered = items

    if (filterImportance !== 'all') {
      filtered = filtered.filter(item => item.importance === filterImportance)
    }

    return filtered
  }, [items, filterImportance])

  // Group items by type
  const groupedItems = useMemo(() => {
    const groups: Record<string, ContextItem[]> = {
      metadata: [],
      node: [],
      edge: []
    }

    filteredItems.forEach(item => {
      groups[item.type].push(item)
    })

    return groups
  }, [filteredItems])

  // Quick actions
  const handleSelectAll = () => {
    const updatedConfig = {
      ...config,
      includeWorkflowMetadata: true,
      includeNodes: true,
      includeEdges: true,
      selectedNodeIds: items.filter(item => item.type === 'node').map(item => item.content.id)
    }
    onConfigChange(updatedConfig)
  }

  const handleDeselectAll = () => {
    const updatedConfig = {
      ...config,
      includeWorkflowMetadata: false,
      includeNodes: false,
      includeEdges: false,
      selectedNodeIds: []
    }
    onConfigChange(updatedConfig)
  }

  const handleOptimize = () => {
    const maxTokens = config.maxTokens || 8000
    const optimized = ContextManager.optimizeForTokenLimit(items, maxTokens)
    
    const selectedNodeIds = optimized
      .filter(item => item.type === 'node' && item.selected)
      .map(item => item.content.id)
    
    const updatedConfig = {
      ...config,
      includeWorkflowMetadata: optimized.some(item => item.type === 'metadata' && item.selected),
      includeNodes: optimized.some(item => item.type === 'node' && item.selected),
      includeEdges: optimized.some(item => item.type === 'edge' && item.selected),
      selectedNodeIds
    }
    onConfigChange(updatedConfig)
  }

  const handleToggleType = (type: 'metadata' | 'node' | 'edge') => {
    const key = type === 'metadata' ? 'includeWorkflowMetadata' : 
                type === 'node' ? 'includeNodes' : 'includeEdges'
    
    onConfigChange({
      ...config,
      [key]: !config[key]
    })
  }

  return (
    <div className={cn('flex flex-col h-full bg-white rounded-lg border border-gray-200', className)}>
      {/* Header */}
      <div className="p-3 border-b border-gray-200">
        <h3 className="font-semibold text-sm mb-3">Context Selection</h3>
        
        {/* Quick Actions */}
        <div className="flex gap-2 flex-wrap">
          <button
            onClick={handleSelectAll}
            className="px-2 py-1 text-xs bg-blue-50 text-blue-700 rounded hover:bg-blue-100 transition-colors"
          >
            Select All
          </button>
          <button
            onClick={handleDeselectAll}
            className="px-2 py-1 text-xs bg-gray-50 text-gray-700 rounded hover:bg-gray-100 transition-colors"
          >
            Deselect All
          </button>
          <button
            onClick={handleOptimize}
            className="px-2 py-1 text-xs bg-green-50 text-green-700 rounded hover:bg-green-100 transition-colors flex items-center gap-1"
          >
            <TrendingUp className="h-3 w-3" />
            Optimize
          </button>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="p-3 border-b border-gray-200 bg-gray-50">
        <div className="flex items-center gap-2 text-xs">
          <Filter className="h-3 w-3 text-gray-500" />
          <span className="text-gray-600">Importance:</span>
          {(['all', 'high', 'medium', 'low'] as const).map(importance => (
            <button
              key={importance}
              onClick={() => setFilterImportance(importance)}
              className={cn(
                'px-2 py-0.5 rounded capitalize',
                filterImportance === importance
                  ? 'bg-blue-100 text-blue-700'
                  : 'bg-white text-gray-600 hover:bg-gray-100'
              )}
            >
              {importance}
            </button>
          ))}
        </div>
      </div>

      {/* Items List */}
      <div className="flex-1 overflow-y-auto p-3 space-y-3">
        {/* Metadata Section */}
        {groupedItems.metadata.length > 0 && (
          <div>
            <div className="flex items-center justify-between mb-2">
              <div className="text-xs font-semibold text-gray-600 flex items-center gap-1">
                <AlertCircle className="h-3 w-3" />
                Workflow Metadata
              </div>
              <button
                onClick={() => handleToggleType('metadata')}
                className="text-xs text-blue-600 hover:text-blue-800"
              >
                {config.includeWorkflowMetadata ? 'Hide' : 'Show'}
              </button>
            </div>
            <div className="space-y-1">
              {groupedItems.metadata.map(item => (
                <ContextItemRow
                  key={item.id}
                  item={item}
                  onToggle={onItemToggle}
                />
              ))}
            </div>
          </div>
        )}

        {/* Nodes Section */}
        {groupedItems.node.length > 0 && (
          <div>
            <div className="flex items-center justify-between mb-2">
              <div className="text-xs font-semibold text-gray-600">
                Nodes ({groupedItems.node.length})
              </div>
              <button
                onClick={() => handleToggleType('node')}
                className="text-xs text-blue-600 hover:text-blue-800"
              >
                {config.includeNodes ? 'Hide All' : 'Show All'}
              </button>
            </div>
            <div className="space-y-1">
              {groupedItems.node.map(item => (
                <ContextItemRow
                  key={item.id}
                  item={item}
                  onToggle={onItemToggle}
                />
              ))}
            </div>
          </div>
        )}

        {/* Edges Section */}
        {groupedItems.edge.length > 0 && (
          <div>
            <div className="flex items-center justify-between mb-2">
              <div className="text-xs font-semibold text-gray-600">
                Edges ({groupedItems.edge.length})
              </div>
              <button
                onClick={() => handleToggleType('edge')}
                className="text-xs text-blue-600 hover:text-blue-800"
              >
                {config.includeEdges ? 'Hide All' : 'Show All'}
              </button>
            </div>
            <div className="space-y-1">
              {groupedItems.edge.map(item => (
                <ContextItemRow
                  key={item.id}
                  item={item}
                  onToggle={onItemToggle}
                />
              ))}
            </div>
          </div>
        )}

        {/* Empty State */}
        {filteredItems.length === 0 && (
          <div className="text-center py-8 text-gray-400 text-sm">
            <Minimize2 className="h-8 w-8 mx-auto mb-2 opacity-50" />
            <p>No items match the filter</p>
          </div>
        )}
      </div>
    </div>
  )
}

/**
 * Individual context item row
 */
interface ContextItemRowProps {
  item: ContextItem
  onToggle: (itemId: string) => void
}

function ContextItemRow({ item, onToggle }: ContextItemRowProps) {
  const importanceColors = {
    high: 'text-red-600 bg-red-50',
    medium: 'text-yellow-600 bg-yellow-50',
    low: 'text-gray-600 bg-gray-50'
  }

  return (
    <div
      className={cn(
        'p-2 rounded border text-xs flex items-center gap-2 cursor-pointer transition-colors',
        item.selected
          ? 'bg-blue-50 border-blue-200'
          : 'bg-white border-gray-200 hover:border-gray-300'
      )}
      onClick={() => onToggle(item.id)}
    >
      {/* Checkbox */}
      <div className="flex-shrink-0">
        {item.selected ? (
          <CheckSquare className="h-4 w-4 text-blue-600" />
        ) : (
          <Square className="h-4 w-4 text-gray-400" />
        )}
      </div>

      {/* Label */}
      <div className="flex-1 min-w-0">
        <div className="font-medium text-gray-900 truncate">
          {item.label}
        </div>
        <div className="text-gray-500 text-[10px]">
          {item.type} · {item.tokens} tokens
        </div>
      </div>

      {/* Importance Badge */}
      <div className={cn(
        'px-1.5 py-0.5 rounded text-[10px] font-medium capitalize',
        importanceColors[item.importance]
      )}>
        {item.importance}
      </div>
    </div>
  )
}
