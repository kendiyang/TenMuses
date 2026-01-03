'use client'

import { useWorkflowStore } from '@/stores/workflow-store'
import { Trash2, Database } from 'lucide-react'
import KnowledgeDocumentSelector from './KnowledgeDocumentSelector'
import { useState } from 'react'

interface PropertiesPanelProps {
  nodeId: string
}

export default function PropertiesPanel({ nodeId }: PropertiesPanelProps) {
  const { nodes, updateNode, deleteNode } = useWorkflowStore()
  const node = nodes.find((n) => n.id === nodeId)
  const [showRagConfig, setShowRagConfig] = useState(false)

  if (!node) return null

  const handleLabelChange = (label: string) => {
    updateNode(nodeId, { label })
  }

  const handlePromptChange = (prompt: string) => {
    updateNode(nodeId, { prompt })
  }

  const handleModelChange = (model: string) => {
    updateNode(nodeId, {
      modelConfig: { ...node.data.modelConfig!, model },
    })
  }

  const handleTemperatureChange = (temperature: number) => {
    updateNode(nodeId, {
      modelConfig: { ...node.data.modelConfig!, temperature },
    })
  }

  // RAG Configuration Handlers
  const handleEnableRagChange = (enableRag: boolean) => {
    updateNode(nodeId, {
      modelConfig: { 
        ...node.data.modelConfig!, 
        enableRag,
        knowledgeDocuments: enableRag ? (node.data.modelConfig?.knowledgeDocuments || []) : [],
      },
    })
    if (enableRag) setShowRagConfig(true)
  }

  const handleKnowledgeDocumentsChange = (knowledgeDocuments: string[]) => {
    updateNode(nodeId, {
      modelConfig: { ...node.data.modelConfig!, knowledgeDocuments },
    })
  }

  const handleRagModeChange = (ragMode: 'document' | 'chunk') => {
    updateNode(nodeId, {
      modelConfig: { ...node.data.modelConfig!, ragMode },
    })
  }

  const handleRagTopKChange = (ragTopK: number) => {
    updateNode(nodeId, {
      modelConfig: { ...node.data.modelConfig!, ragTopK },
    })
  }

  const handleRagMinScoreChange = (ragMinScore: number) => {
    updateNode(nodeId, {
      modelConfig: { ...node.data.modelConfig!, ragMinScore },
    })
  }

  const handleDelete = () => {
    if (confirm('Are you sure you want to delete this node?')) {
      deleteNode(nodeId)
    }
  }

  const isLLMNode = ['llm', 'research', 'writer', 'reviewer'].includes(node.data.type)

  return (
    <div className="p-4">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold">Node Properties</h2>
        <button
          onClick={handleDelete}
          className="p-2 text-red-600 hover:bg-red-50 rounded transition-colors"
          title="Delete node"
        >
          <Trash2 className="w-4 h-4" />
        </button>
      </div>

      <div className="space-y-4">
        {/* Label */}
        <div>
          <label className="block text-sm font-medium mb-1">Label</label>
          <input
            type="text"
            value={node.data.label}
            onChange={(e) => handleLabelChange(e.target.value)}
            className="w-full px-3 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
          />
        </div>

        {/* Type (read-only) */}
        <div>
          <label className="block text-sm font-medium mb-1">Type</label>
          <input
            type="text"
            value={node.data.type}
            disabled
            className="w-full px-3 py-2 border border-border rounded-lg bg-muted"
          />
        </div>

        {/* Model Configuration */}
        <div>
          <label className="block text-sm font-medium mb-1">Model</label>
          <select
            value={node.data.modelConfig?.model || 'gpt-4'}
            onChange={(e) => handleModelChange(e.target.value)}
            className="w-full px-3 py-2 border border-border rounded-lg bg-background"
          >
            <option>gpt-4</option>
            <option>gpt-4-turbo-preview</option>
            <option>gpt-3.5-turbo</option>
            <option>claude-3-sonnet-20240229</option>
            <option>claude-3-opus-20240229</option>
          </select>
        </div>

        {/* RAG Configuration (LLM nodes only) */}
        {isLLMNode && (
          <div className="border-t border-border pt-4 mt-4">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <Database className="w-4 h-4" />
                <label className="text-sm font-medium">Knowledge Base (RAG)</label>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={node.data.modelConfig?.enableRag || false}
                  onChange={(e) => handleEnableRagChange(e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
              </label>
            </div>

            {node.data.modelConfig?.enableRag && (
              <div className="space-y-3 pl-6 border-l-2 border-blue-200">
                {/* Knowledge Documents Selector */}
                <div>
                  <label className="block text-sm font-medium mb-2">Knowledge Documents</label>
                  <KnowledgeDocumentSelector
                    selectedDocumentIds={node.data.modelConfig?.knowledgeDocuments || []}
                    onChange={handleKnowledgeDocumentsChange}
                  />
                </div>

                {/* RAG Mode */}
                <div>
                  <label className="block text-sm font-medium mb-1">Retrieval Mode</label>
                  <select
                    value={node.data.modelConfig?.ragMode || 'chunk'}
                    onChange={(e) => handleRagModeChange(e.target.value as 'document' | 'chunk')}
                    className="w-full px-3 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary text-sm"
                  >
                    <option value="chunk">Chunk (Fine-grained)</option>
                    <option value="document">Document (Whole file)</option>
                  </select>
                  <p className="text-xs text-muted-foreground mt-1">
                    {node.data.modelConfig?.ragMode === 'chunk' 
                      ? 'Retrieve relevant text chunks from documents'
                      : 'Retrieve entire documents'}
                  </p>
                </div>

                {/* Top K */}
                <div>
                  <label className="block text-sm font-medium mb-1">
                    Top K Results: {node.data.modelConfig?.ragTopK || 5}
                  </label>
                  <input
                    type="range"
                    min="1"
                    max="20"
                    step="1"
                    value={node.data.modelConfig?.ragTopK || 5}
                    onChange={(e) => handleRagTopKChange(parseInt(e.target.value))}
                    className="w-full"
                  />
                  <p className="text-xs text-muted-foreground mt-1">
                    Number of {node.data.modelConfig?.ragMode === 'chunk' ? 'chunks' : 'documents'} to retrieve
                  </p>
                </div>

                {/* Min Score */}
                <div>
                  <label className="block text-sm font-medium mb-1">
                    Min Relevance Score: {(node.data.modelConfig?.ragMinScore || 0.5).toFixed(2)}
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.05"
                    value={node.data.modelConfig?.ragMinScore || 0.5}
                    onChange={(e) => handleRagMinScoreChange(parseFloat(e.target.value))}
                    className="w-full"
                  />
                  <p className="text-xs text-muted-foreground mt-1">
                    Filter results below this similarity score (0.0 - 1.0)
                  </p>
                </div>
              </div>
            )}
          </div>
        )}

        {/* value={node.data.modelConfig?.model || 'gpt-4-turbo-preview'}
            onChange={(e) => handleModelChange(e.target.value)}
            className="w-full px-3 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
          >
            <option value="gpt-4-turbo-preview">GPT-4 Turbo</option>
            <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
            <option value="claude-3-sonnet-20240229">Claude 3 Sonnet</option>
            <option value="claude-3-opus-20240229">Claude 3 Opus</option>
          </select>
        </div>

        {/* Temperature */}
        <div>
          <label className="block text-sm font-medium mb-1">
            Temperature: {node.data.modelConfig?.temperature?.toFixed(1) || '0.7'}
          </label>
          <input
            type="range"
            min="0"
            max="2"
            step="0.1"
            value={node.data.modelConfig?.temperature || 0.7}
            onChange={(e) => handleTemperatureChange(parseFloat(e.target.value))}
            className="w-full"
          />
        </div>

        {/* Prompt */}
        <div>
          <label className="block text-sm font-medium mb-1">Prompt</label>
          <textarea
            value={node.data.prompt || ''}
            onChange={(e) => handlePromptChange(e.target.value)}
            rows={6}
            placeholder="Enter the prompt for this node..."
            className="w-full px-3 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary resize-none"
          />
        </div>

        {/* Status (read-only) */}
        <div>
          <label className="block text-sm font-medium mb-1">Status</label>
          <div className="px-3 py-2 border border-border rounded-lg bg-muted">
            <span className="capitalize">{node.data.status}</span>
          </div>
        </div>
      </div>
    </div>
  )
}
