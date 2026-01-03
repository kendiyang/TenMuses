/**
 * ContextPreview Component
 * 
 * Displays analysis and preview of selected context:
 * - Token count and size
 * - Optimization suggestions
 * - Warnings
 * - Content preview
 */

'use client'

import React from 'react'
import { 
  ContextAnalysis, 
  ContextItem,
  ContextManager 
} from '@/lib/context-manager'
import { 
  AlertCircle, 
  CheckCircle, 
  AlertTriangle,
  TrendingUp,
  Info,
  Eye,
  Code
} from 'lucide-react'
import { cn } from '@/lib/utils'

export interface ContextPreviewProps {
  items: ContextItem[]
  analysis: ContextAnalysis
  className?: string
  showContent?: boolean
}

export function ContextPreview({
  items,
  analysis,
  className,
  showContent = false
}: ContextPreviewProps) {
  const [expandedContent, setExpandedContent] = React.useState(false)

  // Calculate percentages
  const tokenPercentage = analysis.totalTokens > 0 
    ? Math.round((analysis.selectedTokens / analysis.totalTokens) * 100) 
    : 0

  const maxTokens = 8000
  const tokenUtilization = Math.round((analysis.selectedTokens / maxTokens) * 100)

  // Status color
  const getStatusColor = () => {
    if (analysis.warnings.length > 0) return 'red'
    if (analysis.suggestions.filter(s => s.severity === 'warning').length > 0) return 'yellow'
    return 'green'
  }

  const statusColor = getStatusColor()

  return (
    <div className={cn('flex flex-col h-full bg-white rounded-lg border border-gray-200', className)}>
      {/* Header */}
      <div className="p-3 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h3 className="font-semibold text-sm">Context Analysis</h3>
          {statusColor === 'green' && (
            <CheckCircle className="h-4 w-4 text-green-600" />
          )}
          {statusColor === 'yellow' && (
            <AlertTriangle className="h-4 w-4 text-yellow-600" />
          )}
          {statusColor === 'red' && (
            <AlertCircle className="h-4 w-4 text-red-600" />
          )}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-3 space-y-3">
        {/* Statistics */}
        <div className="grid grid-cols-2 gap-2">
          <div className="p-3 bg-gray-50 rounded border border-gray-200">
            <div className="text-xs text-gray-600 mb-1">Selected Items</div>
            <div className="text-lg font-semibold text-gray-900">
              {analysis.selectedItems} / {analysis.totalItems}
            </div>
            <div className="text-[10px] text-gray-500">
              {tokenPercentage}% of total
            </div>
          </div>

          <div className="p-3 bg-gray-50 rounded border border-gray-200">
            <div className="text-xs text-gray-600 mb-1">Token Count</div>
            <div className="text-lg font-semibold text-gray-900">
              {analysis.selectedTokens.toLocaleString()}
            </div>
            <div className="text-[10px] text-gray-500">
              ~{Math.round(analysis.selectedSize / 1024)} KB
            </div>
          </div>
        </div>

        {/* Token Usage Bar */}
        <div>
          <div className="flex items-center justify-between text-xs mb-1">
            <span className="text-gray-600">Token Utilization</span>
            <span className={cn(
              'font-medium',
              tokenUtilization > 100 ? 'text-red-600' :
              tokenUtilization > 80 ? 'text-yellow-600' :
              'text-green-600'
            )}>
              {tokenUtilization}%
            </span>
          </div>
          <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
            <div
              className={cn(
                'h-full transition-all',
                tokenUtilization > 100 ? 'bg-red-500' :
                tokenUtilization > 80 ? 'bg-yellow-500' :
                'bg-green-500'
              )}
              style={{ width: `${Math.min(tokenUtilization, 100)}%` }}
            />
          </div>
          <div className="text-[10px] text-gray-500 mt-1">
            {analysis.selectedTokens.toLocaleString()} / {maxTokens.toLocaleString()} tokens
          </div>
        </div>

        {/* Warnings */}
        {analysis.warnings.length > 0 && (
          <div className="space-y-2">
            <div className="text-xs font-semibold text-red-600 flex items-center gap-1">
              <AlertCircle className="h-3 w-3" />
              Warnings
            </div>
            {analysis.warnings.map(warning => (
              <div
                key={warning.id}
                className="p-2 bg-red-50 border border-red-200 rounded text-xs"
              >
                <div className="font-medium text-red-900">{warning.message}</div>
                {warning.affectedItems.length > 0 && (
                  <div className="text-red-700 mt-1 text-[10px]">
                    Affects {warning.affectedItems.length} item(s)
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Suggestions */}
        {analysis.suggestions.length > 0 && (
          <div className="space-y-2">
            <div className="text-xs font-semibold text-blue-600 flex items-center gap-1">
              <TrendingUp className="h-3 w-3" />
              Optimization Suggestions
            </div>
            {analysis.suggestions.map(suggestion => (
              <div
                key={suggestion.id}
                className={cn(
                  'p-2 rounded text-xs border',
                  suggestion.severity === 'error' ? 'bg-red-50 border-red-200' :
                  suggestion.severity === 'warning' ? 'bg-yellow-50 border-yellow-200' :
                  'bg-blue-50 border-blue-200'
                )}
              >
                <div className="flex items-start gap-2">
                  <div className="flex-1">
                    <div className={cn(
                      'font-medium',
                      suggestion.severity === 'error' ? 'text-red-900' :
                      suggestion.severity === 'warning' ? 'text-yellow-900' :
                      'text-blue-900'
                    )}>
                      {suggestion.title}
                    </div>
                    <div className={cn(
                      'mt-0.5',
                      suggestion.severity === 'error' ? 'text-red-700' :
                      suggestion.severity === 'warning' ? 'text-yellow-700' :
                      'text-blue-700'
                    )}>
                      {suggestion.description}
                    </div>
                    {suggestion.impact && (
                      <div className="mt-1 text-[10px] text-gray-600">
                        {suggestion.impact.tokensSaved && (
                          <span>↓ {suggestion.impact.tokensSaved} tokens saved</span>
                        )}
                        {suggestion.impact.tokensAdded && (
                          <span>↑ {suggestion.impact.tokensAdded} tokens added</span>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Success State */}
        {analysis.warnings.length === 0 && analysis.suggestions.length === 0 && (
          <div className="p-3 bg-green-50 border border-green-200 rounded text-xs text-center">
            <CheckCircle className="h-6 w-6 text-green-600 mx-auto mb-1" />
            <div className="font-medium text-green-900">Context Optimized</div>
            <div className="text-green-700 mt-0.5">
              Your context is well-configured
            </div>
          </div>
        )}

        {/* Content Preview */}
        {showContent && (
          <div>
            <button
              onClick={() => setExpandedContent(!expandedContent)}
              className="flex items-center gap-2 text-xs font-semibold text-gray-700 mb-2 hover:text-gray-900"
            >
              <Eye className="h-3 w-3" />
              Content Preview
              <span className="text-gray-500">
                ({expandedContent ? 'hide' : 'show'})
              </span>
            </button>
            
            {expandedContent && (
              <div className="p-2 bg-gray-50 border border-gray-200 rounded">
                <pre className="text-[10px] font-mono text-gray-700 whitespace-pre-wrap max-h-64 overflow-auto">
                  {JSON.stringify(
                    ContextManager.serializeContext(items),
                    null,
                    2
                  )}
                </pre>
              </div>
            )}
          </div>
        )}

        {/* Summary */}
        <div className="p-2 bg-gray-50 border border-gray-200 rounded text-xs">
          <div className="flex items-center gap-1 text-gray-600 mb-1">
            <Info className="h-3 w-3" />
            Context Summary
          </div>
          <div className="text-gray-900">
            {ContextManager.getSummary(items)}
          </div>
        </div>
      </div>
    </div>
  )
}
