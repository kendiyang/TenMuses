'use client'

import { Terminal, Wifi, WifiOff, Database, FileText } from 'lucide-react'
import { useWorkflowStore } from '@/stores/workflow-store'

interface ExecutionPanelProps {
  isConnected?: boolean
  isExecuting?: boolean
  logs?: string[]
}

export default function ExecutionPanel({
  isConnected = false,
  isExecuting = false,
  logs = ['Workflow ready to execute', 'Click "Run" to start execution']
}: ExecutionPanelProps) {
  const nodes = useWorkflowStore((s) => s.nodes)

  const streamingOutputs = nodes.map((n) => ({
    id: n.id,
    label: n.data.label,
    content: n.data.streamingContent || ''
  }))

  return (
    <div className="p-4">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold">Execution</h2>
        <div className="flex items-center gap-2">
          {isConnected ? (
            <>
              <Wifi className="w-4 h-4 text-green-600" />
              <span className="text-sm text-green-600">{isExecuting ? 'Executing' : 'Connected'}</span>
            </>
          ) : (
            <>
              <WifiOff className="w-4 h-4 text-muted-foreground" />
              <span className="text-sm text-muted-foreground">Disconnected</span>
            </>
          )}
        </div>
      </div>

      <div className="space-y-4">
        <div className="p-4 bg-muted rounded-lg">
          <div className="text-sm font-medium mb-1">Status</div>
          <div className={`text-2xl font-bold ${isExecuting ? 'text-blue-600' : 'text-muted-foreground'}`}>
            {isExecuting ? 'Executing' : 'Idle'}
          </div>
        </div>

        <div>
          <div className="flex items-center gap-2 mb-2">
            <Terminal className="w-4 h-4" />
            <span className="text-sm font-medium">Execution Log</span>
          </div>
          <div className="bg-black text-green-400 rounded-lg p-3 font-mono text-xs h-48 overflow-y-auto">
            {logs.map((log, index) => (
              <div key={index} className="mb-1">{log}</div>
            ))}
          </div>
        </div>

        <div>
          <div className="text-sm font-medium mb-2">Streaming Output</div>
          <div className="border border-border rounded-lg p-3 min-h-[100px] text-sm space-y-4">
            {streamingOutputs.length === 0 ? (
              <div className="text-muted-foreground">No output yet. Run the workflow to see results.</div>
            ) : (
              streamingOutputs.map((s) => {
                const node = nodes.find((n) => n.id === s.id)
                const hasRagResults = node?.data.ragSearchResults && node.data.ragSearchResults.length > 0

                return (
                  <div key={s.id} className="space-y-2">
                    <div className="text-xs font-medium">{s.label}</div>
                    
                    {/* RAG Search Results */}
                    {hasRagResults && (
                      <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 space-y-2">
                        <div className="flex items-center gap-2 text-xs font-medium text-blue-700">
                          <Database className="w-3 h-3" />
                          <span>Knowledge Base Results ({node.data.ragSearchResults!.length})</span>
                        </div>
                        <div className="space-y-1.5">
                          {node.data.ragSearchResults!.map((result, idx) => (
                            <div key={idx} className="flex items-start gap-2 text-xs">
                              <FileText className="w-3 h-3 text-blue-600 mt-0.5 flex-shrink-0" />
                              <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-2">
                                  <span className="font-medium text-blue-900 truncate">
                                    {result.title}
                                  </span>
                                  <span className="text-blue-600 font-mono">
                                    {(result.score * 100).toFixed(0)}%
                                  </span>
                                </div>
                                {result.snippet && (
                                  <div className="text-blue-700 text-xs mt-0.5 line-clamp-2">
                                    {result.snippet}
                                  </div>
                                )}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Streaming Content */}
                    <div className="whitespace-pre-wrap text-sm text-muted-foreground">
                      {s.content || <em>No output yet</em>}
                    </div>
                  </div>
                )
              })
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
