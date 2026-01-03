/**
 * TemplatePreview Component
 * 
 * Real-time preview of rendered template with:
 * - Live updates as variables change
 * - Error/warning display
 * - Copy to clipboard
 * - Send to chat functionality
 */

'use client'

import React, { useMemo } from 'react'
import { TemplateEngine, VariableContext, TemplateVariable, RenderResult } from '@/lib/template-engine'
import { AlertCircle, CheckCircle, AlertTriangle, Copy, Send } from 'lucide-react'
import { cn } from '@/lib/utils'

export interface TemplatePreviewProps {
  template: string
  context: VariableContext
  variables?: TemplateVariable[]
  onSend?: (content: string) => void
  className?: string
}

export function TemplatePreview({
  template,
  context,
  variables,
  onSend,
  className
}: TemplatePreviewProps) {
  // Render template
  const renderResult = useMemo<RenderResult>(() => {
    return TemplateEngine.render(template, context, variables)
  }, [template, context, variables])

  // Copy to clipboard
  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(renderResult.content)
      // Could add toast notification here
      console.log('Copied to clipboard')
    } catch (error) {
      console.error('Failed to copy:', error)
    }
  }

  // Send to chat
  const handleSend = () => {
    if (renderResult.isValid && onSend) {
      onSend(renderResult.content)
    }
  }

  return (
    <div className={cn('flex flex-col h-full bg-white rounded-lg border border-gray-200', className)}>
      {/* Header */}
      <div className="flex items-center justify-between p-3 border-b border-gray-200">
        <div>
          <h3 className="font-semibold text-sm">Preview</h3>
          <p className="text-xs text-gray-500 mt-0.5">
            {renderResult.isValid ? 'Ready to use' : 'Has errors'}
          </p>
        </div>
        <div className="flex gap-1">
          <button
            onClick={handleCopy}
            className="p-1.5 hover:bg-gray-100 rounded transition-colors"
            title="Copy to clipboard"
          >
            <Copy className="h-4 w-4" />
          </button>
          {onSend && (
            <button
              onClick={handleSend}
              disabled={!renderResult.isValid}
              className={cn(
                'p-1.5 rounded transition-colors',
                renderResult.isValid
                  ? 'hover:bg-blue-100 text-blue-600'
                  : 'opacity-50 cursor-not-allowed text-gray-400'
              )}
              title="Send to chat"
            >
              <Send className="h-4 w-4" />
            </button>
          )}
        </div>
      </div>

      {/* Status indicator */}
      <div className="px-3 pt-3">
        {renderResult.isValid ? (
          <div className="flex items-center gap-2 text-xs text-green-600 bg-green-50 px-2 py-1.5 rounded">
            <CheckCircle className="h-3 w-3" />
            <span>Template rendered successfully</span>
          </div>
        ) : (
          <div className="flex items-center gap-2 text-xs text-red-600 bg-red-50 px-2 py-1.5 rounded">
            <AlertCircle className="h-3 w-3" />
            <span>{renderResult.errors.length} error(s) found</span>
          </div>
        )}

        {renderResult.warnings.length > 0 && (
          <div className="flex items-center gap-2 text-xs text-yellow-600 bg-yellow-50 px-2 py-1.5 rounded mt-2">
            <AlertTriangle className="h-3 w-3" />
            <span>{renderResult.warnings.length} warning(s)</span>
          </div>
        )}
      </div>

      {/* Rendered content */}
      <div className="flex-1 overflow-y-auto p-3">
        <div className={cn(
          'p-3 rounded-lg border text-sm whitespace-pre-wrap font-mono',
          renderResult.isValid 
            ? 'bg-gray-50 border-gray-200 text-gray-900'
            : 'bg-red-50 border-red-200 text-gray-700'
        )}>
          {renderResult.content || <span className="text-gray-400 italic">Empty template</span>}
        </div>

        {/* Character count */}
        <div className="text-xs text-gray-500 mt-2 text-right">
          {renderResult.content.length} characters
        </div>
      </div>

      {/* Errors section */}
      {renderResult.errors.length > 0 && (
        <div className="p-3 border-t border-gray-200 bg-red-50">
          <div className="text-xs font-semibold text-red-900 mb-2">Errors:</div>
          <ul className="space-y-1 text-xs text-red-700">
            {renderResult.errors.map((error, i) => (
              <li key={i} className="flex items-start gap-1">
                <AlertCircle className="h-3 w-3 mt-0.5 flex-shrink-0" />
                <span>{error}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Warnings section */}
      {renderResult.warnings.length > 0 && (
        <div className="p-3 border-t border-gray-200 bg-yellow-50">
          <div className="text-xs font-semibold text-yellow-900 mb-2">Warnings:</div>
          <ul className="space-y-1 text-xs text-yellow-700">
            {renderResult.warnings.map((warning, i) => (
              <li key={i} className="flex items-start gap-1">
                <AlertTriangle className="h-3 w-3 mt-0.5 flex-shrink-0" />
                <span>{warning}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}

/**
 * Combined Editor + Preview Layout
 */
export interface TemplateEditorWithPreviewProps {
  template: string
  onTemplateChange: (template: string) => void
  context: VariableContext
  onContextChange: (context: VariableContext) => void
  variables?: TemplateVariable[]
  onSend?: (content: string) => void
  className?: string
}

export function TemplateEditorWithPreview({
  template,
  onTemplateChange,
  context,
  onContextChange,
  variables,
  onSend,
  className
}: TemplateEditorWithPreviewProps) {
  // Import editor component
  const { TemplateEditor } = require('./TemplateEditor')
  const { VariablePanel } = require('./VariablePanel')

  // Get template variables
  const parseResult = useMemo(() => {
    return TemplateEngine.parse(template)
  }, [template])

  return (
    <div className={cn('grid grid-cols-2 gap-4 h-full', className)}>
      {/* Left: Editor + Variables */}
      <div className="flex flex-col gap-4">
        <TemplateEditor
          value={template}
          onChange={onTemplateChange}
          height="300px"
        />
        <VariablePanel
          templateVariables={parseResult.variables}
          context={context}
          onContextChange={onContextChange}
          definitions={variables}
          className="flex-1"
        />
      </div>

      {/* Right: Preview */}
      <TemplatePreview
        template={template}
        context={context}
        variables={variables}
        onSend={onSend}
      />
    </div>
  )
}
