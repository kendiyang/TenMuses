'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { Plus, Workflow as WorkflowIcon, Search, Filter, X, Trash2, Copy } from 'lucide-react'
import { apiClient } from '@/lib/api-client'
import { Workflow } from '@/types/workflow'
import { useAuthStore } from '@/stores/auth-store'
import BatchDeleteDialog from '@/components/dialog/BatchDeleteDialog'

export default function WorkflowsPage() {
  const router = useRouter()
  const { isAuthenticated } = useAuthStore()
  const [workflows, setWorkflows] = useState<Workflow[]>([])
  const [filteredWorkflows, setFilteredWorkflows] = useState<Workflow[]>([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [showFilters, setShowFilters] = useState(false)
  const [selectedTags, setSelectedTags] = useState<string[]>([])
  const [selectedWorkflows, setSelectedWorkflows] = useState<Set<string>>(new Set())
  const [showDeleteDialog, setShowDeleteDialog] = useState(false)

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
      applyFilters(data, searchQuery, statusFilter, selectedTags)
    } catch (error) {
      console.error('Failed to load workflows:', error)
    } finally {
      setLoading(false)
    }
  }

  const applyFilters = (
    items: Workflow[],
    search: string,
    status: string,
    tags: string[]
  ) => {
    let filtered = items

    // Search filter
    if (search.trim()) {
      const query = search.toLowerCase()
      filtered = filtered.filter(
        (w) =>
          w.title.toLowerCase().includes(query) ||
          w.description?.toLowerCase().includes(query)
      )
    }

    // Status filter
    if (status !== 'all') {
      filtered = filtered.filter((w) => w.status === status)
    }

    // Tags filter
    if (tags.length > 0) {
      filtered = filtered.filter((w) =>
        tags.some((tag) => w.tags?.includes(tag))
      )
    }

    setFilteredWorkflows(filtered)
  }

  const handleSearchChange = (value: string) => {
    setSearchQuery(value)
    applyFilters(workflows, value, statusFilter, selectedTags)
  }

  const handleStatusChange = (value: string) => {
    setStatusFilter(value)
    applyFilters(workflows, searchQuery, value, selectedTags)
  }

  const handleTagToggle = (tag: string) => {
    const newTags = selectedTags.includes(tag)
      ? selectedTags.filter((t) => t !== tag)
      : [...selectedTags, tag]
    setSelectedTags(newTags)
    applyFilters(workflows, searchQuery, statusFilter, newTags)
  }

  const handleClearFilters = () => {
    setSearchQuery('')
    setStatusFilter('all')
    setSelectedTags([])
    setFilteredWorkflows(workflows)
  }

  const handleToggleWorkflowSelection = (workflowId: string) => {
    const newSelected = new Set(selectedWorkflows)
    if (newSelected.has(workflowId)) {
      newSelected.delete(workflowId)
    } else {
      newSelected.add(workflowId)
    }
    setSelectedWorkflows(newSelected)
  }

  const handleSelectAll = () => {
    if (selectedWorkflows.size === filteredWorkflows.length) {
      setSelectedWorkflows(new Set())
    } else {
      setSelectedWorkflows(new Set(filteredWorkflows.map((w) => w.id)))
    }
  }

  const handleDuplicateSelected = async () => {
    if (selectedWorkflows.size === 0) return

    try {
      for (const id of Array.from(selectedWorkflows)) {
        await apiClient.post(`/workflows/${id}/duplicate`)
      }
      loadWorkflows()
      setSelectedWorkflows(new Set())
    } catch (error) {
      console.error('Failed to duplicate workflows:', error)
    }
  }

  const getSelectedWorkflowTitles = () => {
    const ids = Array.from(selectedWorkflows)
    return filteredWorkflows
      .filter((w) => ids.includes(w.id))
      .map((w) => w.title)
  }

  // Get all unique tags from workflows
  const allTags = Array.from(
    new Set(workflows.flatMap((w) => w.tags || []))
  ).sort()

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

        {/* Batch Operations Bar */}
        {selectedWorkflows.size > 0 && (
          <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg flex items-center justify-between">
            <div className="flex items-center gap-4">
              <span className="text-sm font-medium text-blue-900">
                {selectedWorkflows.size} workflow{selectedWorkflows.size > 1 ? 's' : ''} selected
              </span>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={handleDuplicateSelected}
                className="flex items-center gap-2 px-3 py-2 text-sm border border-blue-300 rounded-lg hover:bg-blue-100 transition-colors"
              >
                <Copy className="w-4 h-4" />
                Duplicate
              </button>
              <button
                onClick={() => setShowDeleteDialog(true)}
                className="flex items-center gap-2 px-3 py-2 text-sm bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
              >
                <Trash2 className="w-4 h-4" />
                Delete
              </button>
              <button
                onClick={() => setSelectedWorkflows(new Set())}
                className="px-3 py-2 text-sm border border-blue-300 rounded-lg hover:bg-blue-100 transition-colors"
              >
                Clear Selection
              </button>
            </div>
          </div>
        )}

        {/* Search and Filter Section */}
        <div className="space-y-4 mb-6">
          {/* Search Bar */}
          <div className="flex gap-2">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <input
                type="text"
                placeholder="Search workflows..."
                value={searchQuery}
                onChange={(e) => handleSearchChange(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/50"
              />
            </div>
            <button
              onClick={() => setShowFilters(!showFilters)}
              className="px-4 py-2 border border-border rounded-lg hover:bg-accent transition-colors flex items-center gap-2"
            >
              <Filter className="w-4 h-4" />
              <span className="hidden sm:inline">Filters</span>
              {searchQuery || statusFilter !== 'all' || selectedTags.length > 0 ? (
                <span className="ml-1 px-2 py-0.5 text-xs bg-primary text-primary-foreground rounded-full">
                  {selectedTags.length + (statusFilter !== 'all' ? 1 : 0)}
                </span>
              ) : null}
            </button>
          </div>

          {/* Filters Panel */}
          {showFilters && (
            <div className="p-4 border border-border rounded-lg bg-muted/50 space-y-4">
              {/* Status Filter */}
              <div>
                <label className="block text-sm font-medium mb-2">Status</label>
                <select
                  value={statusFilter}
                  onChange={(e) => handleStatusChange(e.target.value)}
                  className="w-full px-3 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/50"
                >
                  <option value="all">All Status</option>
                  <option value="draft">Draft</option>
                  <option value="published">Published</option>
                  <option value="running">Running</option>
                </select>
              </div>

              {/* Tags Filter */}
              {allTags.length > 0 && (
                <div>
                  <label className="block text-sm font-medium mb-2">Tags</label>
                  <div className="flex flex-wrap gap-2">
                    {allTags.map((tag) => (
                      <button
                        key={tag}
                        onClick={() => handleTagToggle(tag)}
                        className={`px-3 py-1 text-sm rounded-full transition-colors ${
                          selectedTags.includes(tag)
                            ? 'bg-primary text-primary-foreground'
                            : 'bg-background border border-border hover:border-primary'
                        }`}
                      >
                        {tag}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Clear Filters */}
              {(searchQuery || statusFilter !== 'all' || selectedTags.length > 0) && (
                <button
                  onClick={handleClearFilters}
                  className="w-full px-3 py-2 text-sm border border-border rounded-lg hover:bg-accent transition-colors flex items-center justify-center gap-2"
                >
                  <X className="w-4 h-4" />
                  Clear All Filters
                </button>
              )}
            </div>
          )}
        </div>

        {/* Workflows Grid */}
        {filteredWorkflows.length > 0 && (
          <div className="mb-4 flex items-center gap-2">
            <input
              type="checkbox"
              checked={selectedWorkflows.size === filteredWorkflows.length && filteredWorkflows.length > 0}
              onChange={handleSelectAll}
              className="w-4 h-4 cursor-pointer"
              title="Select all workflows on this page"
            />
            <span className="text-sm text-muted-foreground">
              Select All ({filteredWorkflows.length})
            </span>
          </div>
        )}

        {/* Workflows Grid */}
        {filteredWorkflows.length === 0 ? (
          <div className="text-center py-16">
            <WorkflowIcon className="w-16 h-16 mx-auto mb-4 text-muted-foreground" />
            <h2 className="text-xl font-semibold mb-2">
              {workflows.length === 0 ? 'No workflows yet' : 'No workflows match your search'}
            </h2>
            <p className="text-muted-foreground mb-6">
              {workflows.length === 0
                ? 'Create your first AI workflow to get started'
                : 'Try adjusting your search or filters'}
            </p>
            {workflows.length === 0 && (
              <button
                onClick={createWorkflow}
                className="px-6 py-3 bg-primary text-primary-foreground rounded-lg hover:opacity-90 transition-opacity"
              >
                Create Workflow
              </button>
            )}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredWorkflows.map((workflow) => (
              <div
                key={workflow.id}
                className={`relative p-6 border rounded-lg transition-all hover:shadow-lg ${
                  selectedWorkflows.has(workflow.id)
                    ? 'border-primary bg-primary/5'
                    : 'border-border hover:border-primary'
                }`}
              >
                {/* Checkbox */}
                <input
                  type="checkbox"
                  checked={selectedWorkflows.has(workflow.id)}
                  onChange={() => handleToggleWorkflowSelection(workflow.id)}
                  className="absolute top-4 right-4 w-4 h-4 cursor-pointer"
                  onClick={(e) => e.stopPropagation()}
                />

                <Link
                  href={`/workflows/${workflow.id}`}
                  className="block"
                >
                <div className="flex items-start justify-between mb-2">
                  <h3 className="text-lg font-semibold flex-1">{workflow.title}</h3>
                  {workflow.status && (
                    <span
                      className={`text-xs font-medium px-2 py-1 rounded-full ml-2 whitespace-nowrap ${
                        workflow.status === 'published'
                          ? 'bg-green-100 text-green-800'
                          : workflow.status === 'running'
                          ? 'bg-blue-100 text-blue-800'
                          : 'bg-gray-100 text-gray-800'
                      }`}
                    >
                      {workflow.status}
                    </span>
                  )}
                </div>
                <p className="text-sm text-muted-foreground mb-4">
                  {workflow.description || 'No description'}
                </p>
                <div className="flex items-center justify-between text-xs text-muted-foreground">
                  <span>
                    {workflow.canvasJson?.nodes?.length || 0} nodes
                  </span>
                  {workflow.last_run_at && (
                    <span>
                      Last run: {new Date(workflow.last_run_at).toLocaleDateString()}
                    </span>
                  )}
                </div>
                {workflow.tags && workflow.tags.length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-4">
                    {workflow.tags.slice(0, 3).map((tag) => (
                      <span
                        key={tag}
                        className="inline-block px-2 py-1 text-xs bg-primary/10 text-primary rounded"
                      >
                        {tag}
                      </span>
                    ))}
                    {workflow.tags.length > 3 && (
                      <span className="text-xs text-muted-foreground px-2 py-1">
                        +{workflow.tags.length - 3} more
                      </span>
                    )}
                  </div>
                )}
                </Link>
              </div>
            ))}
          </div>
        )}

        {/* Delete Dialog */}
        {showDeleteDialog && selectedWorkflows.size > 0 && (
          <BatchDeleteDialog
            workflowIds={Array.from(selectedWorkflows)}
            workflowTitles={getSelectedWorkflowTitles()}
            onClose={() => setShowDeleteDialog(false)}
            onSuccess={() => {
              loadWorkflows()
              setSelectedWorkflows(new Set())
            }}
          />
        )}
      </div>
    </div>
  )
}
