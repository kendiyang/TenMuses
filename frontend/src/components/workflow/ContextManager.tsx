/**
 * ContextManager Component
 * 
 * Combined context selector and preview interface
 */

'use client'

import React from 'react'
import { Node, Edge } from 'reactflow'
import { useContextManager } from '@/hooks/useContextManager'
import { ContextSelector } from './ContextSelector'
import { ContextPreview } from './ContextPreview'
import { cn } from '@/lib/utils'

export interface ContextManagerProps {
  nodes: Node[]
  edges: Edge[]
  metadata?: Record<string, any>
  onContextChange?: (context: any) => void
  className?: string
  layout?: 'horizontal' | 'vertical'
}

export function ContextManagerComponent({
  nodes,
  edges,
  metadata,
  onContextChange,
  className,
  layout = 'horizontal'
}: ContextManagerProps) {
  const {
    items,
    config,
    analysis,
    updateConfig,
    toggleItem,
    serialize
  } = useContextManager({
    nodes,
    edges,
    metadata
  })

  // Notify parent of context changes
  React.useEffect(() => {
    if (onContextChange) {
      onContextChange(serialize())
    }
  }, [items, onContextChange, serialize])

  if (layout === 'vertical') {
    return (
      <div className={cn('flex flex-col gap-4 h-full', className)}>
        <div className="flex-1 min-h-0">
          <ContextSelector
            items={items}
            config={config}
            onConfigChange={updateConfig}
            onItemToggle={toggleItem}
          />
        </div>
        <div className="flex-1 min-h-0">
          <ContextPreview
            items={items}
            analysis={analysis}
            showContent={true}
          />
        </div>
      </div>
    )
  }

  return (
    <div className={cn('grid grid-cols-2 gap-4 h-full', className)}>
      <ContextSelector
        items={items}
        config={config}
        onConfigChange={updateConfig}
        onItemToggle={toggleItem}
      />
      <ContextPreview
        items={items}
        analysis={analysis}
        showContent={true}
      />
    </div>
  )
}
