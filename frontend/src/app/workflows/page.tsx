'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { Plus, Workflow as WorkflowIcon } from 'lucide-react'
import { apiClient } from '@/lib/api-client'
import { Workflow } from '@/types/workflow'
import { useAuthStore } from '@/stores/auth-store'

export default function WorkflowsPage() {
  const router = useRouter()
  const { isAuthenticated } = useAuthStore()
  const [workflows, setWorkflows] = useState<Workflow[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/auth/login')
      return
    }
    loadWorkflows()
  }, [isAuthenticated, router])

  const loadWorkflows = async () => {
    try {
      const data = await apiClient.get<Workflow[]>('/workflows')
      setWorkflows(data)
    } catch (error) {
      console.error('Failed to load workflows:', error)
    } finally {
      setLoading(false)
    }
  }

  const createWorkflow = async () => {
    try {
      const workflow = await apiClient.post<Workflow>('/workflows', {
        title: 'New Workflow',
        description: 'A new AI workflow',
        is_public: false,
      })
      router.push(`/workflows/${workflow.id}`)
    } catch (error) {
      console.error('Failed to create workflow:', error)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-lg">Loading...</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto px-4 py-8">
        <div className="flex items-center justify-between mb-8">
          <h1 className="text-3xl font-bold">My Workflows</h1>
          <button
            onClick={createWorkflow}
            className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:opacity-90 transition-opacity"
          >
            <Plus className="w-5 h-5" />
            New Workflow
          </button>
        </div>

        {workflows.length === 0 ? (
          <div className="text-center py-16">
            <WorkflowIcon className="w-16 h-16 mx-auto mb-4 text-muted-foreground" />
            <h2 className="text-xl font-semibold mb-2">No workflows yet</h2>
            <p className="text-muted-foreground mb-6">
              Create your first AI workflow to get started
            </p>
            <button
              onClick={createWorkflow}
              className="px-6 py-3 bg-primary text-primary-foreground rounded-lg hover:opacity-90 transition-opacity"
            >
              Create Workflow
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {workflows.map((workflow) => (
              <Link
                key={workflow.id}
                href={`/workflows/${workflow.id}`}
                className="block p-6 border border-border rounded-lg hover:border-primary transition-colors"
              >
                <h3 className="text-lg font-semibold mb-2">{workflow.title}</h3>
                <p className="text-sm text-muted-foreground mb-4">
                  {workflow.description || 'No description'}
                </p>
                <div className="flex items-center justify-between text-xs text-muted-foreground">
                  <span>
                    {workflow.canvasJson?.nodes?.length || 0} nodes
                  </span>
                  <span>
                    {new Date(workflow.updatedAt).toLocaleDateString()}
                  </span>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
