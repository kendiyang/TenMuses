import { useEffect, useRef, useState, useCallback } from 'react'
import { WebSocketClient } from '@/lib/websocket-client'
import { WSEvent } from '@/types/websocket'
import { useWorkflowStore } from '@/stores/workflow-store'

export function useWorkflowExecution(threadId: string | null) {
  const wsClient = useRef<WebSocketClient | null>(null)
  const [isConnected, setIsConnected] = useState(false)
  const [isExecuting, setIsExecuting] = useState(false)
  const [logs, setLogs] = useState<string[]>([])
  const { updateNode, appendNodeStreamingContent } = useWorkflowStore()

  const addLog = useCallback((message: string) => {
    setLogs((prev) => [...prev, `[${new Date().toLocaleTimeString()}] ${message}`])
  }, [])

  const handleEvent = useCallback((event: WSEvent) => {
    console.log('WebSocket event:', event)

    switch (event.type) {
      case 'connected':
        addLog('Connected to execution stream')
        setIsConnected(true)
        break

      case 'run_started':
        addLog(`Workflow started: ${event.payload.inputSummary}`)
        setIsExecuting(true)
        break

      case 'node_started':
        addLog(`Node started: ${event.payload.label}`)
        if (event.nodeId) {
          updateNode(event.nodeId, { status: 'executing', streamingContent: '' })
        }
        break

      case 'node_status':
        if (event.nodeId) {
          updateNode(event.nodeId, { status: event.payload.status })
        }
        break

      case 'token':
        if (event.nodeId && event.payload.content) {
          // Append token content to node's streamingContent
          appendNodeStreamingContent(event.nodeId, event.payload.content)
        }
        break

      case 'rag_search' as any:
        if (event.nodeId) {
          addLog(`RAG: Retrieved ${event.payload.documentCount} documents for node ${event.payload.nodeId || event.nodeId}`)
          // Update node with RAG search results
          updateNode(event.nodeId, {
            ragSearchResults: event.payload.results || [],
          })
        }
        break

      case 'run_completed':
        addLog('Workflow completed successfully')
        setIsExecuting(false)
        break

      case 'error':
        addLog(`Error: ${event.payload.message}`)
        setIsExecuting(false)
        if (event.nodeId) {
          updateNode(event.nodeId, {
            status: 'error',
            error: event.payload.message,
          })
        }
        break
    }
  }, [addLog, updateNode, appendNodeStreamingContent])

  const connect = useCallback(async (tid?: string) => {
    const id = tid ?? threadId
    if (!id || wsClient.current) return

    const client = new WebSocketClient()
    wsClient.current = client

    client.on('*', handleEvent)

    try {
      await client.connect(id)
    } catch (error) {
      console.error('Failed to connect:', error)
      addLog('Failed to connect to execution stream')
    }
  }, [threadId, handleEvent, addLog])

  const startExecution = useCallback(async (input: string) => {
    if (!wsClient.current || !wsClient.current.isConnected()) {
      addLog('Not connected to execution stream')
      return
    }

    // Send start command
    const ws = (wsClient.current as any).ws
    if (ws) {
      ws.send(JSON.stringify({
        action: 'start',
        input,
      }))
    }
  }, [addLog])

  const disconnect = useCallback(() => {
    if (wsClient.current) {
      wsClient.current.disconnect()
      wsClient.current = null
      setIsConnected(false)
      setIsExecuting(false)
    }
  }, [])

  useEffect(() => {
    return () => {
      disconnect()
    }
  }, [disconnect])

  return {
    isConnected,
    isExecuting,
    logs,
    connect,
    startExecution,
    disconnect,
  }
}
