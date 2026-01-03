/**
 * VariablePanel Component
 * 
 * Manages template variables:
 * - Display all detected variables
 * - Edit variable values
 * - Add custom variables
 * - System variables
 */

'use client'

import React, { useState, useCallback } from 'react'
import { 
  TemplateVariable, 
  VariableContext, 
  VariableType,
  SYSTEM_VARIABLES 
} from '@/lib/template-engine'
import { Plus, Trash2, Edit2, Check, X, Info } from 'lucide-react'
import { cn } from '@/lib/utils'

export interface VariablePanelProps {
  templateVariables: string[]  // Variables detected in template
  context: VariableContext
  onContextChange: (context: VariableContext) => void
  definitions?: TemplateVariable[]
  onDefinitionsChange?: (definitions: TemplateVariable[]) => void
  className?: string
}

export function VariablePanel({
  templateVariables,
  context,
  onContextChange,
  definitions = [],
  onDefinitionsChange,
  className
}: VariablePanelProps) {
  const [editingVar, setEditingVar] = useState<string | null>(null)
  const [editValue, setEditValue] = useState('')
  const [showAddDialog, setShowAddDialog] = useState(false)

  // Update variable value in context
  const handleValueChange = useCallback((varName: string, value: string) => {
    const newContext = { ...context, [varName]: value }
    onContextChange(newContext)
  }, [context, onContextChange])

  // Start editing a variable
  const startEdit = useCallback((varName: string) => {
    setEditingVar(varName)
    setEditValue(String(context[varName] || ''))
  }, [context])

  // Save edit
  const saveEdit = useCallback(() => {
    if (editingVar) {
      handleValueChange(editingVar, editValue)
      setEditingVar(null)
      setEditValue('')
    }
  }, [editingVar, editValue, handleValueChange])

  // Cancel edit
  const cancelEdit = useCallback(() => {
    setEditingVar(null)
    setEditValue('')
  }, [])

  // Remove variable from context
  const removeVariable = useCallback((varName: string) => {
    const newContext = { ...context }
    delete newContext[varName]
    onContextChange(newContext)
  }, [context, onContextChange])

  // Get variable definition if exists
  const getDefinition = useCallback((varName: string): TemplateVariable | undefined => {
    return definitions.find(d => d.name === varName) ||
           SYSTEM_VARIABLES.find(d => d.name === varName)
  }, [definitions])

  // Categorize variables
  const systemVars = templateVariables.filter(v => 
    SYSTEM_VARIABLES.some(sys => sys.name === v)
  )
  const customVars = templateVariables.filter(v => 
    !SYSTEM_VARIABLES.some(sys => sys.name === v)
  )

  return (
    <div className={cn('flex flex-col h-full bg-white rounded-lg border border-gray-200', className)}>
      {/* Header */}
      <div className="flex items-center justify-between p-3 border-b border-gray-200">
        <div>
          <h3 className="font-semibold text-sm">Variables</h3>
          <p className="text-xs text-gray-500 mt-0.5">
            {templateVariables.length} detected in template
          </p>
        </div>
        <button
          onClick={() => setShowAddDialog(true)}
          className="p-1.5 hover:bg-gray-100 rounded transition-colors"
          title="Add custom variable"
        >
          <Plus className="h-4 w-4" />
        </button>
      </div>

      {/* Variable list */}
      <div className="flex-1 overflow-y-auto p-3 space-y-4">
        {/* System Variables */}
        {systemVars.length > 0 && (
          <div>
            <div className="text-xs font-semibold text-gray-600 mb-2 flex items-center gap-1">
              <Info className="h-3 w-3" />
              System Variables
            </div>
            <div className="space-y-2">
              {systemVars.map(varName => {
                const def = getDefinition(varName)
                const value = context[varName]
                const isEditing = editingVar === varName

                return (
                  <div
                    key={varName}
                    className="p-2 bg-blue-50 border border-blue-200 rounded text-xs"
                  >
                    <div className="flex items-center justify-between mb-1">
                      <div className="font-mono font-semibold text-blue-900">
                        {varName}
                      </div>
                      {!isEditing && (
                        <button
                          onClick={() => startEdit(varName)}
                          className="p-1 hover:bg-blue-100 rounded"
                          title="Edit value"
                        >
                          <Edit2 className="h-3 w-3" />
                        </button>
                      )}
                    </div>

                    {def?.description && (
                      <div className="text-gray-600 mb-2">{def.description}</div>
                    )}

                    {isEditing ? (
                      <div className="flex gap-1">
                        <input
                          type="text"
                          value={editValue}
                          onChange={(e) => setEditValue(e.target.value)}
                          className="flex-1 px-2 py-1 border border-blue-300 rounded text-xs"
                          autoFocus
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') saveEdit()
                            if (e.key === 'Escape') cancelEdit()
                          }}
                        />
                        <button
                          onClick={saveEdit}
                          className="p-1 bg-green-500 text-white rounded hover:bg-green-600"
                        >
                          <Check className="h-3 w-3" />
                        </button>
                        <button
                          onClick={cancelEdit}
                          className="p-1 bg-gray-400 text-white rounded hover:bg-gray-500"
                        >
                          <X className="h-3 w-3" />
                        </button>
                      </div>
                    ) : (
                      <div className="font-mono text-gray-700 bg-white px-2 py-1 rounded border border-blue-200">
                        {value || <span className="text-gray-400">(not set)</span>}
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          </div>
        )}

        {/* Custom Variables */}
        {customVars.length > 0 && (
          <div>
            <div className="text-xs font-semibold text-gray-600 mb-2">
              Custom Variables
            </div>
            <div className="space-y-2">
              {customVars.map(varName => {
                const def = getDefinition(varName)
                const value = context[varName]
                const isEditing = editingVar === varName

                return (
                  <div
                    key={varName}
                    className="p-2 bg-gray-50 border border-gray-200 rounded text-xs"
                  >
                    <div className="flex items-center justify-between mb-1">
                      <div className="font-mono font-semibold text-gray-900">
                        {varName}
                      </div>
                      <div className="flex gap-1">
                        {!isEditing && (
                          <>
                            <button
                              onClick={() => startEdit(varName)}
                              className="p-1 hover:bg-gray-200 rounded"
                              title="Edit value"
                            >
                              <Edit2 className="h-3 w-3" />
                            </button>
                            <button
                              onClick={() => removeVariable(varName)}
                              className="p-1 hover:bg-red-100 text-red-600 rounded"
                              title="Remove variable"
                            >
                              <Trash2 className="h-3 w-3" />
                            </button>
                          </>
                        )}
                      </div>
                    </div>

                    {def?.description && (
                      <div className="text-gray-600 mb-2">{def.description}</div>
                    )}

                    {isEditing ? (
                      <div className="flex gap-1">
                        <input
                          type="text"
                          value={editValue}
                          onChange={(e) => setEditValue(e.target.value)}
                          className="flex-1 px-2 py-1 border border-gray-300 rounded text-xs"
                          autoFocus
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') saveEdit()
                            if (e.key === 'Escape') cancelEdit()
                          }}
                        />
                        <button
                          onClick={saveEdit}
                          className="p-1 bg-green-500 text-white rounded hover:bg-green-600"
                        >
                          <Check className="h-3 w-3" />
                        </button>
                        <button
                          onClick={cancelEdit}
                          className="p-1 bg-gray-400 text-white rounded hover:bg-gray-500"
                        >
                          <X className="h-3 w-3" />
                        </button>
                      </div>
                    ) : (
                      <div className="font-mono text-gray-700 bg-white px-2 py-1 rounded border border-gray-200">
                        {value || <span className="text-gray-400">(not set)</span>}
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          </div>
        )}

        {/* Empty state */}
        {templateVariables.length === 0 && (
          <div className="text-center py-8 text-gray-400 text-sm">
            <Info className="h-8 w-8 mx-auto mb-2 opacity-50" />
            <p>No variables detected</p>
            <p className="text-xs mt-1">Use {`{{variableName}}`} in template</p>
          </div>
        )}
      </div>

      {/* Add variable dialog */}
      {showAddDialog && (
        <AddVariableDialog
          existingVariables={Object.keys(context)}
          onAdd={(varName, value) => {
            handleValueChange(varName, value)
            setShowAddDialog(false)
          }}
          onCancel={() => setShowAddDialog(false)}
        />
      )}
    </div>
  )
}

/**
 * Dialog for adding a new variable
 */
interface AddVariableDialogProps {
  existingVariables: string[]
  onAdd: (name: string, value: string) => void
  onCancel: () => void
}

function AddVariableDialog({ existingVariables, onAdd, onCancel }: AddVariableDialogProps) {
  const [name, setName] = useState('')
  const [value, setValue] = useState('')
  const [error, setError] = useState('')

  const handleAdd = () => {
    // Validate name
    if (!name.trim()) {
      setError('Variable name is required')
      return
    }

    if (!/^[a-zA-Z_][a-zA-Z0-9_]*$/.test(name)) {
      setError('Invalid variable name (use letters, numbers, underscore)')
      return
    }

    if (existingVariables.includes(name)) {
      setError('Variable already exists')
      return
    }

    onAdd(name, value)
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-4 w-96 max-w-full mx-4">
        <h3 className="text-sm font-semibold mb-3">Add Custom Variable</h3>
        
        <div className="space-y-3">
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">
              Variable Name
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => {
                setName(e.target.value)
                setError('')
              }}
              placeholder="myVariable"
              className="w-full px-2 py-1.5 border border-gray-300 rounded text-sm"
              autoFocus
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">
              Default Value
            </label>
            <input
              type="text"
              value={value}
              onChange={(e) => setValue(e.target.value)}
              placeholder="Enter default value"
              className="w-full px-2 py-1.5 border border-gray-300 rounded text-sm"
            />
          </div>

          {error && (
            <div className="text-xs text-red-600 bg-red-50 px-2 py-1 rounded">
              {error}
            </div>
          )}

          <div className="flex gap-2 justify-end pt-2">
            <button
              onClick={onCancel}
              className="px-3 py-1.5 text-sm border border-gray-300 rounded hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              onClick={handleAdd}
              className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              Add Variable
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
