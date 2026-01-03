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
import { Save, Play, Settings, Sparkles, BarChart3, PanelLeft, PanelLeftOpen, PanelRight, PanelRightOpen, Share2, Upload, Home, ChevronDown } from 'lucide-react'

interface PageProps {
  params: { id: string }
}

type RightPanelTab = 'properties' | 'execution' | 'copilot'

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
  const [rightPanelTab, setRightPanelTab] = useState<RightPanelTab>('execution')
  const [showLeftPanel, setShowLeftPanel] = useState(true)
  const [showRightPanel, setShowRightPanel] = useState(true)
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
        {/* Left Sidebar - Node Toolbar */}
        {showLeftPanel && (
          <div className="w-64 border-r border-border overflow-y-auto relative">
            <div className="absolute top-2 right-2 z-10">
              <button
                onClick={() => setShowLeftPanel(false)}
                className="flex items-center gap-1 rounded border border-border bg-white/90 px-2 py-1 text-xs text-muted-foreground hover:text-foreground hover:border-primary shadow-sm"
              >
                <PanelLeft className="w-4 h-4" />
                隐藏
              </button>
            </div>
            <NodeToolbar />
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

        {/* Canvas */}
        <div className="flex-1 relative">
          <WorkflowCanvas onNodeSelect={setSelectedNodeId} />
        </div>

        {/* Right Sidebar - Properties, Execution, or Copilot */}
        {showRightPanel && (
          <div className="w-80 border-l border-border flex flex-col overflow-hidden relative">
            {/* Tab Navigation */}
            <div className="flex border-b border-border bg-muted/50 items-center">
            {/* Properties Tab */}
            {selectedNodeId && (
              <button
                onClick={() => setRightPanelTab('properties')}
                className={`flex-1 py-2 px-3 text-xs font-medium transition-colors flex items-center justify-center gap-2 border-b-2 -mb-px ${
                  rightPanelTab === 'properties'
                    ? 'text-foreground border-primary bg-background'
                    : 'text-muted-foreground border-transparent hover:text-foreground'
                }`}
              >
                <Settings className="w-3.5 h-3.5" />
                <span className="hidden sm:inline">Properties</span>
              </button>
            )}

            {/* Execution Tab */}
            <button
              onClick={() => setRightPanelTab('execution')}
              className={`flex-1 py-2 px-3 text-xs font-medium transition-colors flex items-center justify-center gap-2 border-b-2 -mb-px ${
                rightPanelTab === 'execution'
                  ? 'text-foreground border-primary bg-background'
                  : 'text-muted-foreground border-transparent hover:text-foreground'
              }`}
            >
              <BarChart3 className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Execution</span>
            </button>

            {/* Copilot Tab */}
            <button
              onClick={() => setRightPanelTab('copilot')}
              className={`flex-1 py-2 px-3 text-xs font-medium transition-colors flex items-center justify-center gap-2 border-b-2 -mb-px ${
                rightPanelTab === 'copilot'
                  ? 'text-foreground border-primary bg-background'
                  : 'text-muted-foreground border-transparent hover:text-foreground'
              }`}
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Copilot</span>
            </button>

              <button
                onClick={() => setShowRightPanel(false)}
                className="px-3 py-2 text-muted-foreground hover:text-foreground transition-colors"
                title="隐藏右栏"
              >
                <PanelRight className="w-4 h-4" />
              </button>
            </div>

            {/* Tab Content */}
            <div className="flex-1 overflow-y-auto">
              {rightPanelTab === 'properties' && selectedNodeId && (
                <PropertiesPanel nodeId={selectedNodeId} />
              )}

              {rightPanelTab === 'execution' && (
                <ExecutionPanel
                  isConnected={isConnected}
                  isExecuting={isExecuting}
                  logs={logs}
                />
              )}

              {rightPanelTab === 'copilot' && (
                <CopilotPanel
                  workflowId={id}
                  onNodeApply={handleNodeApply}
                  onWorkflowApply={handleWorkflowApply}
                />
              )}
            </div>
          </div>
        )}

        {!showRightPanel && (
          <button
            onClick={() => setShowRightPanel(true)}
            className="absolute right-3 top-3 z-20 flex items-center gap-1 rounded border border-border bg-white/95 px-2 py-1 text-xs text-muted-foreground hover:text-foreground hover:border-primary shadow"
          >
            <PanelRightOpen className="w-4 h-4" />
            展开右栏
          </button>
        )}
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
