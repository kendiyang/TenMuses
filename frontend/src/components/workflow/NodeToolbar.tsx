'use client'

import { Brain, FileText, CheckCircle } from 'lucide-react'
import { useWorkflowStore } from '@/stores/workflow-store'
import { Node } from 'reactflow'
import { AgentNodeData } from '@/types/workflow'

const nodeTemplates = [
  {
    type: 'research' as const,
    label: 'Research',
    icon: Brain,
    description: 'Search and gather information',
  },
  {
    type: 'writer' as const,
    label: 'Writer',
    icon: FileText,
    description: 'Generate content based on input',
  },
  {
    type: 'reviewer' as const,
    label: 'Reviewer',
    icon: CheckCircle,
    description: 'Review and refine content',
  },
]

export default function NodeToolbar() {
  const { addNode } = useWorkflowStore()

  const handleAddNode = (template: typeof nodeTemplates[0]) => {
    const newNode: Node<AgentNodeData> = {
      id: `${template.type}-${Date.now()}`,
      type: 'agent',
      position: { x: Math.random() * 400, y: Math.random() * 400 },
      data: {
        label: template.label,
        type: template.type,
        status: 'idle',
        modelConfig: {
          provider: 'openai',
          model: 'gpt-4-turbo-preview',
          temperature: 0.7,
        },
        prompt: '',
      },
    }
    addNode(newNode)
  }

  return (
    <div className="p-4">
      <h2 className="text-lg font-semibold mb-4">Add Nodes</h2>
      
      <div className="space-y-2">
        {nodeTemplates.map((template) => {
          const Icon = template.icon
          return (
            <button
              key={template.type}
              onClick={() => handleAddNode(template)}
              className="w-full p-3 border border-border rounded-lg hover:border-primary hover:bg-accent transition-colors text-left"
            >
              <div className="flex items-center gap-3 mb-1">
                <Icon className="w-5 h-5" />
                <span className="font-medium">{template.label}</span>
              </div>
              <p className="text-xs text-muted-foreground">
                {template.description}
              </p>
            </button>
          )
        })}
      </div>
    </div>
  )
}
