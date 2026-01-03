/**
 * TemplateEditor Component
 * 
 * A syntax-highlighted editor for prompt templates with:
 * - Variable placeholder highlighting
 * - Auto-completion suggestions
 * - Error highlighting
 * - Line numbers
 */

'use client'

import React, { useState, useRef, useEffect, useCallback } from 'react'
import { TemplateEngine, type ParseResult } from '@/lib/template-engine'
import { AlertCircle, CheckCircle, Info } from 'lucide-react'
import { cn } from '@/lib/utils'

export interface TemplateEditorProps {
  value: string
  onChange: (value: string) => void
  onParse?: (result: ParseResult) => void
  placeholder?: string
  className?: string
  height?: string | number
  showLineNumbers?: boolean
  readonly?: boolean
}

export function TemplateEditor({
  value,
  onChange,
  onParse,
  placeholder = 'Enter your prompt template here...\n\nUse {{variableName}} for variables\nUse {{variableName:defaultValue}} for variables with defaults',
  className,
  height = '300px',
  showLineNumbers = true,
  readonly = false
}: TemplateEditorProps) {
  const [parseResult, setParseResult] = useState<ParseResult | null>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const highlightRef = useRef<HTMLDivElement>(null)

  // Parse template on value change
  useEffect(() => {
    const result = TemplateEngine.parse(value)
    setParseResult(result)
    onParse?.(result)
  }, [value, onParse])

  // Sync scroll between textarea and highlight layer
  const handleScroll = useCallback(() => {
    if (textareaRef.current && highlightRef.current) {
      highlightRef.current.scrollTop = textareaRef.current.scrollTop
      highlightRef.current.scrollLeft = textareaRef.current.scrollLeft
    }
  }, [])

  // Highlight template syntax
  const getHighlightedContent = useCallback(() => {
    if (!value) return ''

    // Split by variable placeholders
    const parts: string[] = []
    let lastIndex = 0
    const regex = /\{\{([^}]+)\}\}/g
    let match: RegExpExecArray | null

    while ((match = regex.exec(value)) !== null) {
      // Add text before placeholder
      if (match.index > lastIndex) {
        parts.push(escapeHtml(value.substring(lastIndex, match.index)))
      }

      // Add highlighted placeholder
      const varContent = match[1]
      const varName = varContent.split(':')[0].trim()
      const hasDefault = varContent.includes(':')
      
      // Check if variable name is valid
      const isValid = /^[a-zA-Z_][a-zA-Z0-9_]*$/.test(varName)
      const className = isValid ? 'text-blue-600 font-semibold' : 'text-red-600 font-semibold'
      
      parts.push(
        `<span class="${className} bg-blue-50 px-1 rounded">{{${escapeHtml(varContent)}}}</span>`
      )

      lastIndex = match.index + match[0].length
    }

    // Add remaining text
    if (lastIndex < value.length) {
      parts.push(escapeHtml(value.substring(lastIndex)))
    }

    return parts.join('')
  }, [value])

  // Handle textarea input
  const handleInput = useCallback((e: React.ChangeEvent<HTMLTextAreaElement>) => {
    onChange(e.target.value)
  }, [onChange])

  // Handle tab key for indentation
  const handleKeyDown = useCallback((e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Tab') {
      e.preventDefault()
      const textarea = textareaRef.current
      if (!textarea) return

      const start = textarea.selectionStart
      const end = textarea.selectionEnd
      const newValue = value.substring(0, start) + '  ' + value.substring(end)
      
      onChange(newValue)
      
      // Restore cursor position after state update
      setTimeout(() => {
        textarea.selectionStart = textarea.selectionEnd = start + 2
      }, 0)
    }
  }, [value, onChange])

  // Get line numbers
  const lineNumbers = value.split('\n').map((_, i) => i + 1)

  return (
    <div className={cn('flex flex-col', className)}>
      {/* Editor container */}
      <div 
        className="relative border border-gray-300 rounded-lg overflow-hidden bg-white"
        style={{ height }}
      >
        <div className="flex h-full">
          {/* Line numbers */}
          {showLineNumbers && (
            <div className="flex-shrink-0 w-12 bg-gray-50 border-r border-gray-200 text-right pr-2 pt-2 text-xs text-gray-500 font-mono select-none overflow-hidden">
              {lineNumbers.map(num => (
                <div key={num} className="leading-6">
                  {num}
                </div>
              ))}
            </div>
          )}

          {/* Editor area */}
          <div className="flex-1 relative">
            {/* Syntax highlight layer */}
            <div
              ref={highlightRef}
              className="absolute inset-0 p-2 font-mono text-sm leading-6 whitespace-pre-wrap break-words overflow-auto pointer-events-none"
              style={{ 
                color: 'transparent',
                caretColor: 'black'
              }}
              dangerouslySetInnerHTML={{ __html: getHighlightedContent() }}
            />

            {/* Textarea */}
            <textarea
              ref={textareaRef}
              value={value}
              onChange={handleInput}
              onScroll={handleScroll}
              onKeyDown={handleKeyDown}
              placeholder={placeholder}
              readOnly={readonly}
              className={cn(
                'absolute inset-0 w-full h-full p-2 font-mono text-sm leading-6',
                'bg-transparent resize-none outline-none',
                'text-gray-900 caret-gray-900',
                'placeholder:text-gray-400',
                readonly && 'cursor-not-allowed'
              )}
              style={{
                color: 'transparent',
                caretColor: 'black'
              }}
              spellCheck={false}
            />
          </div>
        </div>
      </div>

      {/* Status bar */}
      <div className="mt-2 flex items-center justify-between text-xs">
        <div className="flex items-center gap-3">
          {parseResult && (
            <>
              {parseResult.isValid ? (
                <div className="flex items-center gap-1 text-green-600">
                  <CheckCircle className="h-3 w-3" />
                  <span>Valid template</span>
                </div>
              ) : (
                <div className="flex items-center gap-1 text-red-600">
                  <AlertCircle className="h-3 w-3" />
                  <span>{parseResult.errors.length} error(s)</span>
                </div>
              )}

              {parseResult.variables.length > 0 && (
                <div className="flex items-center gap-1 text-blue-600">
                  <Info className="h-3 w-3" />
                  <span>{parseResult.variables.length} variable(s)</span>
                </div>
              )}
            </>
          )}
        </div>

        <div className="text-gray-500">
          {value.length} characters, {value.split('\n').length} lines
        </div>
      </div>

      {/* Error messages */}
      {parseResult && parseResult.errors.length > 0 && (
        <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded text-xs text-red-700">
          <div className="font-semibold mb-1">Errors:</div>
          <ul className="list-disc list-inside space-y-1">
            {parseResult.errors.map((error, i) => (
              <li key={i}>{error}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Variable list */}
      {parseResult && parseResult.isValid && parseResult.variables.length > 0 && (
        <div className="mt-2 p-2 bg-blue-50 border border-blue-200 rounded text-xs">
          <div className="font-semibold text-blue-900 mb-1">Variables used:</div>
          <div className="flex flex-wrap gap-1">
            {parseResult.variables.map(varName => (
              <span
                key={varName}
                className="px-2 py-0.5 bg-blue-100 text-blue-700 rounded font-mono"
              >
                {varName}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

/**
 * Escape HTML special characters
 */
function escapeHtml(text: string): string {
  const div = document.createElement('div')
  div.textContent = text
  return div.innerHTML
}

/**
 * Quick template insertion buttons
 */
export interface QuickTemplateProps {
  onInsert: (template: string) => void
  className?: string
}

export function QuickTemplates({ onInsert, className }: QuickTemplateProps) {
  const templates = [
    {
      name: 'Workflow Suggestion',
      template: 'Please suggest a {{workflowType:RAG}} workflow for {{task}}.\n\nRequirements:\n- {{requirement1}}\n- {{requirement2}}\n\nCurrent context: {{context}}'
    },
    {
      name: 'Node Configuration',
      template: 'Configure {{nodeType}} node for {{purpose}}.\n\nParameters:\n- Input: {{inputType}}\n- Output: {{outputType}}\n- Model: {{modelName:gpt-4}}'
    },
    {
      name: 'Code Review',
      template: 'Review the following {{language}} code:\n\n{{code}}\n\nFocus on:\n- {{aspect1:performance}}\n- {{aspect2:security}}\n- {{aspect3:maintainability}}'
    },
    {
      name: 'Documentation',
      template: 'Generate documentation for {{component}}.\n\nInclude:\n- Overview\n- Parameters: {{parameters}}\n- Examples\n- Related: {{relatedComponents}}'
    }
  ]

  return (
    <div className={cn('space-y-2', className)}>
      <div className="text-xs font-semibold text-gray-700">Quick Templates:</div>
      <div className="grid grid-cols-2 gap-2">
        {templates.map((t, i) => (
          <button
            key={i}
            onClick={() => onInsert(t.template)}
            className="p-2 text-left text-xs border border-gray-200 rounded hover:border-blue-400 hover:bg-blue-50 transition-colors"
          >
            <div className="font-medium text-gray-900">{t.name}</div>
            <div className="text-gray-500 mt-0.5 truncate">
              {TemplateEngine.getVariableCount(t.template)} variables
            </div>
          </button>
        ))}
      </div>
    </div>
  )
}
