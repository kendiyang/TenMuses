'use client'

import { use, useCallback, useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { apiClient } from '@/lib/api-client'
import { Workflow } from '@/types/workflow'
import { useAuthStore } from '@/stores/auth-store'
import { useWorkflowStore } from '@/stores/workflow-store'
import { useWorkflowExecution } from '@/hooks/useWorkflowExecution'
import WorkflowCanvas from '@/components/workflow/WorkflowCanvas'
import NodeToolbar from '@/components/workflow/NodeToolbar'
import PropertiesPanel from '@/components/workflow/PropertiesPanel'
import ExecutionPanel from '@/components/workflow/ExecutionPanel'
import { CopilotPanel } from '@/components/workflow/CopilotPanel'
import PublishTemplateDialog from '@/components/dialog/PublishTemplateDialog'
import ShareWorkflowDialog from '@/components/dialog/ShareWorkflowDialog'
import { Save, Play, Settings, Sparkles, BarChart3, PanelLeft, PanelLeftOpen, Share2, Upload, Home, ChevronDown, Edit3, Activity } from 'lucide-react'

interface PageProps {
  params: { id: string }
}

export default function WorkflowPage({ params }: PageProps) {
  const { id } = params
  const router = useRouter()
  const { isAuthenticated } = useAuthStore()
  const { setNodes, setEdges, setViewport, nodes, edges, addNode } = useWorkflowStore()
  
  const [workflow, setWorkflow] = useState<Workflow | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null)
  const [threadId, setThreadId] = useState<string | null>(null)
  const [canvasTab, setCanvasTab] = useState<'editor' | 'execution'>('editor')
  const [showLeftPanel, setShowLeftPanel] = useState(true)
  const [showPublishDialog, setShowPublishDialog] = useState(false)
  const [showShareDialog, setShowShareDialog] = useState(false)
  
  const { isConnected, isExecuting, logs, connect, startExecution } = useWorkflowExecution(threadId)

  const loadWorkflow = useCallback(async () => {
    try {
      const data = await apiClient.get<Workflow>(`/workflows/${id}`)
      setWorkflow(data)
      
      // Load canvas state
      if (data.canvasJson) {
        setNodes(data.canvasJson.nodes || [])
        setEdges(data.canvasJson.edges || [])
        setViewport(data.canvasJson.viewport || { x: 0, y: 0, zoom: 1 })
      }
    } catch (error) {
      console.error('Failed to load workflow:', error)
      router.push('/workflows')
    } finally {
      setLoading(false)
    }
  }, [id, router, setNodes, setEdges, setViewport])

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/auth/login')
      return
    }
    loadWorkflow()
  }, [isAuthenticated, loadWorkflow, router])

  const saveWorkflow = async () => {
    if (!workflow) return
    
    setSaving(true)
    try {
      await apiClient.put(`/workflows/${id}`, {
        canvas_json: {
          nodes,
          edges,
          viewport: { x: 0, y: 0, zoom: 1 },
        },
      })
    } catch (error) {
      console.error('Failed to save workflow:', error)
    } finally {
      setSaving(false)
    }
  }

  const runWorkflow = async () => {
    try {
      // Create a new run
      const run = await apiClient.post<{ thread_id: string }>(`/workflows/${id}/run`, {
        input: 'Generate an article about AI trends',
        initial_state: {},
        start_server_side: true,
      })

      // Set thread ID locally
      setThreadId(run.thread_id)

      // Connect explicitly using the returned thread id (server will start execution)
      await connect(run.thread_id)

      console.log('Workflow started:', run)
    } catch (error) {
      console.error('Failed to run workflow:', error)
    }
  }

  /**
   * 处理节点建议应用
   */
  const handleNodeApply = useCallback(
    (node: any) => {
      try {
        // 生成唯一 ID
        const nodeId = `node_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`

        // 创建节点对象
        const newNode = {
          id: nodeId,
          data: {
            label: node.label || node.type,
            type: node.type,
            config: node.config || {},
            description: node.description || '',
            status: 'idle' as const,
          },
          position: {
            x: Math.random() * 200 + 250,
            y: Math.random() * 200 + 100,
          },
          type: 'agent',
        }

        // 添加到画布
        addNode(newNode)

        // 显示成功提示
        console.log('✅ 节点已添加:', node.label)
      } catch (error) {
        console.error('❌ 添加节点失败:', error)
      }
    },
    [addNode]
  )

  /**
   * 处理工作流建议应用
   */
  const handleWorkflowApply = useCallback(
    (workflow: any) => {
      try {
        // 确认替换
        if (!confirm('要替换当前工作流吗?')) return

        // 加载工作流
        const newNodes = (workflow.nodes || []).map((node: any, idx: number) => ({
          id: node.id || `node_${idx}`,
          data: {
            label: node.label || node.type,
            type: node.type,
            config: node.config || {},
            description: node.description || '',
            status: 'idle' as const,
          },
          position: node.position || {
            x: (idx % 3) * 300 + 50,
            y: Math.floor(idx / 3) * 150 + 50,
          },
          type: 'agent',
        }))

        const newEdges = (workflow.edges || []).map((edge: any) => ({
          id: `${edge.source}-${edge.target}`,
          source: edge.source,
          target: edge.target,
          sourceHandle: edge.sourceHandle,
          targetHandle: edge.targetHandle,
        }))

        // 更新状态
        setNodes(newNodes)
        setEdges(newEdges)

        console.log('✅ 工作流已加载:', workflow.name)
      } catch (error) {
        console.error('❌ 加载工作流失败:', error)
      }
    },
    [setNodes, setEdges]
  )

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-lg">Loading workflow...</div>
      </div>
    )
  }

  if (!workflow) {
    return null
  }

  return (
    <div className="h-screen flex flex-col bg-background">
      {/* Header */}
      <div className="h-14 border-b border-border flex items-center justify-between px-4">
        <div className="flex items-center gap-4">
          {/* Home/Workspace Navigation Dropdown */}
          <div className="relative group">
            <button
              onClick={() => router.push('/workspace')}
              className="flex items-center gap-2 px-3 py-2 rounded-lg border border-border hover:bg-accent transition-colors"
              title="Return to Workspace"
            >
              <Home className="w-4 h-4" />
              <ChevronDown className="w-3 h-3" />
            </button>
            
            {/* Dropdown menu */}
            <div className="absolute left-0 top-full mt-1 hidden group-hover:block z-50">
              <div className="bg-background border border-border rounded-lg shadow-xl py-1 min-w-[160px]">
                <button
                  onClick={() => router.push('/workspace')}
                  className="w-full text-left px-4 py-2 text-sm hover:bg-accent transition-colors flex items-center gap-2"
                >
                  <Home className="w-4 h-4" />
                  Workspace
                </button>
                <button
                  onClick={() => router.push('/workflows')}
                  className="w-full text-left px-4 py-2 text-sm hover:bg-accent transition-colors"
                >
                  My Workflows
                </button>
                <button
                  onClick={() => router.push('/marketplace')}
                  className="w-full text-left px-4 py-2 text-sm hover:bg-accent transition-colors"
                >
                  Marketplace
                </button>
              </div>
            </div>
          </div>
          
          <div className="h-6 w-px bg-border"></div>
          
          <h1 className="text-lg font-semibold">{workflow.title}</h1>
        </div>
        
        <div className="flex items-center gap-2">
          <button
            onClick={saveWorkflow}
            disabled={saving}
            className="flex items-center gap-2 px-4 py-2 text-sm border border-border rounded-lg hover:bg-accent transition-colors disabled:opacity-50"
          >
            <Save className="w-4 h-4" />
            {saving ? 'Saving...' : 'Save'}
          </button>
          <button
            onClick={() => setShowPublishDialog(true)}
            className="flex items-center gap-2 px-4 py-2 text-sm border border-border rounded-lg hover:bg-accent transition-colors"
            title="Publish this workflow as a template for others to use"
          >
            <Upload className="w-4 h-4" />
            <span className="hidden sm:inline">Publish</span>
          </button>
          <button
            onClick={() => setShowShareDialog(true)}
            className="flex items-center gap-2 px-4 py-2 text-sm border border-border rounded-lg hover:bg-accent transition-colors"
            title="Share this workflow with others via link"
          >
            <Share2 className="w-4 h-4" />
            <span className="hidden sm:inline">Share</span>
          </button>
          <button
            onClick={runWorkflow}
            className="flex items-center gap-2 px-4 py-2 text-sm bg-primary text-primary-foreground rounded-lg hover:opacity-90 transition-opacity"
          >
            <Play className="w-4 h-4" />
            Run
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden relative">
        {/* Left Sidebar - Copilot Only */}
        {showLeftPanel && (
          <div className="w-64 border-r border-border flex flex-col overflow-hidden relative">
            {/* Header */}
            <div className="flex items-center justify-between gap-1 border-b border-border px-2 py-2">
              <div className="flex items-center gap-2">
                <Sparkles className="w-3.5 h-3.5" />
                <span className="text-xs font-medium">Copilot</span>
              </div>
              <button
                onClick={() => setShowLeftPanel(false)}
                className="p-1 text-gray-500 hover:text-gray-900 transition-colors hover:bg-gray-100 rounded"
                title="隐藏左栏"
              >
                <PanelLeft className="w-4 h-4" />
              </button>
            </div>

            {/* Tab Content */}
            <div className="flex-1 overflow-y-auto">
              <CopilotPanel
                workflowId={id}
                onNodeApply={handleNodeApply}
                onWorkflowApply={handleWorkflowApply}
              />
            </div>
          </div>
        )}

        {!showLeftPanel && (
          <button
            onClick={() => setShowLeftPanel(true)}
            className="absolute left-3 top-3 z-20 flex items-center gap-1 rounded border border-border bg-white/95 px-2 py-1 text-xs text-muted-foreground hover:text-foreground hover:border-primary shadow"
          >
            <PanelLeftOpen className="w-4 h-4" />
            展开左栏
          </button>
        )}

        {/* Canvas Area with Top Tabs */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Canvas Top Bar - Editor / Execution Tabs */}
          <div className="flex items-center justify-center border-b border-border py-2 px-4">
            <div className="inline-flex items-center bg-gray-100 rounded-md p-0.5">
              <button
                onClick={() => setCanvasTab('editor')}
                className={`py-1 px-3 text-sm font-medium transition-all rounded ${
                  canvasTab === 'editor'
                    ? 'bg-white text-gray-900 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                Editor
              </button>
              <button
                onClick={() => setCanvasTab('execution')}
                className={`py-1 px-3 text-sm font-medium transition-all rounded ${
                  canvasTab === 'execution'
                    ? 'bg-white text-gray-900 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                Execution
              </button>
            </div>
          </div>

          {/* Canvas Content */}
          <div className="flex-1 relative flex overflow-hidden">
            {canvasTab === 'editor' && (
              <>
                <div className="flex-1 relative">
                  <WorkflowCanvas onNodeSelect={setSelectedNodeId} />
                </div>
                
                {/* Properties Panel (only shown when node selected) */}
                {selectedNodeId && (
                  <div className="w-80 border-l border-border overflow-y-auto">
                    <div className="p-3 border-b border-border bg-muted/50 flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Settings className="w-4 h-4" />
                        <span className="text-sm font-medium">Properties</span>
                      </div>
                      <button
                        onClick={() => setSelectedNodeId(null)}
                        className="text-muted-foreground hover:text-foreground transition-colors"
                        title="关闭"
                      >
                        ×
                      </button>
                    </div>
                    <PropertiesPanel nodeId={selectedNodeId} />
                  </div>
                )}
              </>
            )}

            {canvasTab === 'execution' && (
              <div className="flex-1 overflow-hidden">
                <ExecutionPanel
                  isConnected={isConnected}
                  isExecuting={isExecuting}
                  logs={logs}
                />
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Publish Template Dialog */}
      {showPublishDialog && workflow && (
        <PublishTemplateDialog
          workflowId={id}
          workflowTitle={workflow.title}
          onClose={() => setShowPublishDialog(false)}
          onSuccess={() => {
            // Optionally reload workflow or show success message
            loadWorkflow()
          }}
        />
      )}

      {/* Share Workflow Dialog */}
      {showShareDialog && workflow && (
        <ShareWorkflowDialog
          workflowId={id}
          workflowTitle={workflow.title}
          onClose={() => setShowShareDialog(false)}
          onSuccess={() => {
            // Dialog will handle success state
          }}
        />
      )}
    </div>
  )
}
