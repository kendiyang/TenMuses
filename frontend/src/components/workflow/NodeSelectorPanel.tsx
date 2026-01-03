'use client'

import { useState } from 'react'
import { X, Search, Zap, Calendar, Webhook, FileText, GitBranch, MessageSquare, FolderOpen, Brain } from 'lucide-react'

interface NodeOption {
  id: string
  icon: React.ComponentType<{ className?: string }>
  title: string
  description: string
  type: 'llm' | 'tool' | 'router' | 'map' | 'research' | 'writer' | 'reviewer'
  hasArrow?: boolean
}

const nodeOptions: NodeOption[] = [
  {
    id: 'trigger-manual',
    icon: Zap,
    title: 'Trigger manually',
    description: 'Runs the flow on clicking a button in n8n. Good for getting started quickly',
    type: 'llm',
  },
  {
    id: 'app-event',
    icon: Webhook,
    title: 'On app event',
    description: 'Runs the flow when something happens in an app like Telegram, Notion or Airtable',
    type: 'tool',
    hasArrow: true,
  },
  {
    id: 'schedule',
    icon: Calendar,
    title: 'On a schedule',
    description: 'Runs the flow every day, hour, or custom interval',
    type: 'research',
  },
  {
    id: 'webhook',
    icon: Webhook,
    title: 'On webhook call',
    description: 'Runs the flow on receiving an HTTP request',
    type: 'tool',
  },
  {
    id: 'form-submission',
    icon: FileText,
    title: 'On form submission',
    description: 'Generate webforms in n8n and pass their responses to the workflow',
    type: 'writer',
  },
  {
    id: 'workflow-call',
    icon: GitBranch,
    title: 'When executed by another workflow',
    description: 'Runs the flow when called by the Execute Workflow node from a different workflow',
    type: 'router',
  },
  {
    id: 'chat-message',
    icon: MessageSquare,
    title: 'On chat message',
    description: 'Runs the flow when a user sends a chat message. For use with AI nodes',
    type: 'llm',
  },
  {
    id: 'other-ways',
    icon: FolderOpen,
    title: 'Other ways...',
    description: 'Runs the flow on workflow errors, file changes, etc.',
    type: 'map',
    hasArrow: true,
  },
]

interface NodeSelectorPanelProps {
  onClose: () => void
  onSelectNode: (nodeType: NodeOption['type'], nodeId: string) => void
  position?: { x: number; y: number }
}

export default function NodeSelectorPanel({ onClose, onSelectNode, position }: NodeSelectorPanelProps) {
  const [searchQuery, setSearchQuery] = useState('')

  const filteredOptions = nodeOptions.filter(
    (option) =>
      option.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      option.description.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const handleSelectNode = (option: NodeOption) => {
    onSelectNode(option.type, option.id)
    onClose()
  }

  return (
    <>
      {/* Backdrop */}
      <div className="fixed inset-0 z-40" onClick={onClose} />

      {/* Panel */}
      <div
        className="fixed z-50 w-[400px] bg-white rounded-lg shadow-2xl overflow-hidden"
        style={{
          top: position?.y || '100px',
          right: '20px',
          maxHeight: 'calc(100vh - 40px)',
        }}
      >
        {/* Header */}
        <div className="p-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold mb-1">What triggers this workflow?</h3>
          <p className="text-sm text-gray-500">A trigger is a step that starts your workflow</p>
        </div>

        {/* Search */}
        <div className="p-4 border-b border-gray-200">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search nodes..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              autoFocus
            />
          </div>
        </div>

        {/* Options List */}
        <div className="max-h-[500px] overflow-y-auto">
          {filteredOptions.map((option) => {
            const Icon = option.icon
            return (
              <button
                key={option.id}
                onClick={() => handleSelectNode(option)}
                className="w-full p-4 flex items-start gap-3 hover:bg-gray-50 transition-colors border-b border-gray-100 text-left"
              >
                <div className="flex-shrink-0 w-8 h-8 flex items-center justify-center">
                  <Icon className="w-5 h-5 text-gray-600" />
                </div>
                <div className="flex-1 min-w-0">
                  <h4 className="text-sm font-medium text-gray-900">{option.title}</h4>
                  <p className="text-xs text-gray-500 mt-0.5 line-clamp-2">{option.description}</p>
                </div>
                {option.hasArrow && (
                  <div className="flex-shrink-0">
                    <svg className="w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </div>
                )}
              </button>
            )
          })}
        </div>
      </div>
    </>
  )
}
