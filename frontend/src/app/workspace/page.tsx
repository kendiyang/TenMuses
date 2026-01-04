'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { Plus, BookOpen, Clock, ChevronRight, TrendingUp, Zap } from 'lucide-react'
import { apiClient } from '@/lib/api-client'
import { Workflow } from '@/types/workflow'
import { useAuthStore } from '@/stores/auth-store'
import { useWorkspaceStore } from '@/stores/workspace-store'

export default function WorkspacePage() {
  const router = useRouter()
  const { isAuthenticated, user } = useAuthStore()
  const {
    recentWorkflows,
    statistics,
    isLoadingOverview,
    overviewError,
    fetchWorkspaceOverview,
  } = useWorkspaceStore()

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/auth/login')
      return
    }
    // Load workspace data on mount
    fetchWorkspaceOverview()
  }, [isAuthenticated, router, fetchWorkspaceOverview])

  const createWorkflow = async () => {
    try {
      const workflow = await apiClient.post<Workflow>('/workflows', {
        title: 'Untitled',
        description: 'A new AI workflow',
        is_public: false,
      })
      router.push(`/workflows/${workflow.id}`)
    } catch (error) {
      console.error('Failed to create workflow:', error)
    }
  }

  if (isLoadingOverview) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-lg">Loading workspace...</div>
      </div>
    )
  }

  if (overviewError) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen gap-4">
        <div className="text-lg text-destructive">Error loading workspace</div>
        <p className="text-sm text-muted-foreground">{overviewError}</p>
        <button
          onClick={fetchWorkspaceOverview}
          className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90"
        >
          Retry
        </button>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto px-6 py-8 max-w-7xl space-y-12">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">
              Welcome back, {user?.username || 'User'}!
            </h1>
            <p className="text-muted-foreground mt-1">
              Manage your AI workflows and explore the marketplace
            </p>
          </div>
          <button
            onClick={createWorkflow}
            className="flex items-center gap-2 px-6 py-3 bg-primary text-primary-foreground rounded-xl hover:bg-primary/90 font-medium shadow-lg transition-all"
          >
            <Plus className="w-5 h-5" />
            New Workflow
          </button>
        </div>

        {/* Statistics Cards */}
        {statistics && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="p-6 bg-gradient-to-br from-blue-500/10 to-blue-600/10 rounded-xl border border-blue-500/20">
              <div className="flex items-center gap-3 mb-2">
                <div className="p-2 bg-blue-500/20 rounded-lg">
                  <Zap className="w-5 h-5 text-blue-600" />
                </div>
                <h3 className="text-sm font-medium text-muted-foreground">Total Workflows</h3>
              </div>
              <p className="text-3xl font-bold">{statistics.total_workflows}</p>
            </div>

            <div className="p-6 bg-gradient-to-br from-green-500/10 to-green-600/10 rounded-xl border border-green-500/20">
              <div className="flex items-center gap-3 mb-2">
                <div className="p-2 bg-green-500/20 rounded-lg">
                  <TrendingUp className="w-5 h-5 text-green-600" />
                </div>
                <h3 className="text-sm font-medium text-muted-foreground">Total Runs</h3>
              </div>
              <p className="text-3xl font-bold">{statistics.total_runs}</p>
            </div>

            <div className="p-6 bg-gradient-to-br from-purple-500/10 to-purple-600/10 rounded-xl border border-purple-500/20">
              <div className="flex items-center gap-3 mb-2">
                <div className="p-2 bg-purple-500/20 rounded-lg">
                  <BookOpen className="w-5 h-5 text-purple-600" />
                </div>
                <h3 className="text-sm font-medium text-muted-foreground">Templates Used</h3>
              </div>
              <p className="text-3xl font-bold">{statistics.total_templates}</p>
            </div>
          </div>
        )}

        {/* Recent Workflows */}
        <section>
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-semibold">Recent Workflows</h2>
            <Link
              href="/workflows"
              className="text-sm text-muted-foreground hover:text-foreground flex items-center gap-1"
            >
              View all
              <ChevronRight className="w-4 h-4" />
            </Link>
          </div>

          {recentWorkflows.length === 0 ? (
            <div className="text-center py-12 border border-dashed border-border rounded-xl">
              <p className="text-muted-foreground mb-4">No recent workflows</p>
              <button
                onClick={createWorkflow}
                className="text-primary hover:underline"
              >
                Create your first workflow
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {recentWorkflows.map((workflow) => (
                <Link
                  key={workflow.id}
                  href={`/workflows/${workflow.id}`}
                  className="p-6 border border-border rounded-xl hover:border-primary hover:shadow-md transition-all group"
                >
                  <div className="flex items-start justify-between mb-2">
                    <h3 className="text-lg font-semibold group-hover:text-primary transition-colors">
                      {workflow.title}
                    </h3>
                    {workflow.status && (
                      <span className={`text-xs px-2 py-1 rounded-full ${
                        workflow.status === 'published' ? 'bg-green-500/20 text-green-600' :
                        workflow.status === 'running' ? 'bg-blue-500/20 text-blue-600' :
                        'bg-gray-500/20 text-gray-600'
                      }`}>
                        {workflow.status}
                      </span>
                    )}
                  </div>
                  {workflow.description && (
                    <p className="text-sm text-muted-foreground mb-3 line-clamp-2">
                      {workflow.description}
                    </p>
                  )}
                  <div className="flex items-center gap-4 text-sm text-muted-foreground">
                    <div className="flex items-center gap-1">
                      <Clock className="w-4 h-4" />
                      <span>
                        {workflow.last_run_at
                          ? new Date(workflow.last_run_at).toLocaleDateString()
                          : new Date(workflow.updated_at).toLocaleDateString()}
                      </span>
                    </div>
                    {workflow.nodes_count > 0 && (
                      <span>{workflow.nodes_count} nodes</span>
                    )}
                    {workflow.tags && workflow.tags.length > 0 && (
                      <div className="flex gap-1">
                        {workflow.tags.slice(0, 2).map((tag) => (
                          <span key={tag} className="px-2 py-0.5 bg-accent rounded text-xs">
                            {tag}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                </Link>
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  )
}
