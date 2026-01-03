import { create } from 'zustand'
import { Node, Edge, applyNodeChanges, applyEdgeChanges, NodeChange, EdgeChange } from 'reactflow'
import { AgentNodeData, CanvasViewport } from '@/types/workflow'

interface WorkflowStore {
  nodes: Node<AgentNodeData>[]
  edges: Edge[]
  viewport: CanvasViewport
  
  // Actions
  setNodes: (nodes: Node<AgentNodeData>[]) => void
  setEdges: (edges: Edge[]) => void
  setViewport: (viewport: CanvasViewport) => void
  onNodesChange: (changes: NodeChange[]) => void
  onEdgesChange: (changes: EdgeChange[]) => void
  addNode: (node: Node<AgentNodeData>) => void
  updateNode: (nodeId: string, data: Partial<AgentNodeData>) => void
  appendNodeStreamingContent: (nodeId: string, content: string) => void
  deleteNode: (nodeId: string) => void
  addEdge: (edge: Edge) => void
  deleteEdge: (edgeId: string) => void
  reset: () => void
}

const initialViewport: CanvasViewport = { x: 0, y: 0, zoom: 1 }

export const useWorkflowStore = create<WorkflowStore>((set, get) => ({
  nodes: [],
  edges: [],
  viewport: initialViewport,

  setNodes: (nodes) => set({ nodes }),
  
  setEdges: (edges) => set({ edges }),
  
  setViewport: (viewport) => set({ viewport }),

  onNodesChange: (changes) => {
    set({
      nodes: applyNodeChanges(changes, get().nodes),
    })
  },

  onEdgesChange: (changes) => {
    set({
      edges: applyEdgeChanges(changes, get().edges),
    })
  },

  addNode: (node) => {
    set({ nodes: [...get().nodes, node] })
  },

  updateNode: (nodeId, data) => {
    set({
      nodes: get().nodes.map((node) =>
        node.id === nodeId
          ? { ...node, data: { ...node.data, ...data } }
          : node
      ),
    })
  },

  appendNodeStreamingContent: (nodeId: string, content: string) => {
    set({
      nodes: get().nodes.map((node) =>
        node.id === nodeId
          ? { ...node, data: { ...node.data, streamingContent: (node.data.streamingContent || '') + content } }
          : node
      ),
    })
  },

  deleteNode: (nodeId) => {
    set({
      nodes: get().nodes.filter((node) => node.id !== nodeId),
      edges: get().edges.filter(
        (edge) => edge.source !== nodeId && edge.target !== nodeId
      ),
    })
  },

  addEdge: (edge) => {
    set({ edges: [...get().edges, edge] })
  },

  deleteEdge: (edgeId) => {
    set({
      edges: get().edges.filter((edge) => edge.id !== edgeId),
    })
  },

  reset: () => {
    set({
      nodes: [],
      edges: [],
      viewport: initialViewport,
    })
  },
}))
