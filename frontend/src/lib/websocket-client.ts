import { WSEvent } from '@/types/websocket'

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000'

export class WebSocketClient {
  private ws: WebSocket | null = null
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 1000
  private listeners: Map<string, Set<(event: WSEvent) => void>> = new Map()

  connect(threadId: string): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        this.ws = new WebSocket(`${WS_URL}/api/v1/ws/run/${threadId}`)

        this.ws.onopen = () => {
          console.log(`WebSocket connected for thread: ${threadId}`)
          this.reconnectAttempts = 0
          resolve()
        }

        this.ws.onmessage = (event) => {
          try {
            const wsEvent: WSEvent = JSON.parse(event.data)
            this.notifyListeners(wsEvent)
          } catch (error) {
            console.error('Failed to parse WebSocket message:', error)
          }
        }

        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error)
          reject(error)
        }

        this.ws.onclose = () => {
          console.log('WebSocket closed')
          this.attemptReconnect(threadId)
        }
      } catch (error) {
        reject(error)
      }
    })
  }

  private attemptReconnect(threadId: string): void {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++
      console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`)
      
      setTimeout(() => {
        this.connect(threadId).catch((error) => {
          console.error('Reconnection failed:', error)
        })
      }, this.reconnectDelay * this.reconnectAttempts)
    } else {
      console.error('Max reconnection attempts reached')
    }
  }

  on(eventType: string, callback: (event: WSEvent) => void): void {
    if (!this.listeners.has(eventType)) {
      this.listeners.set(eventType, new Set())
    }
    this.listeners.get(eventType)!.add(callback)
  }

  off(eventType: string, callback: (event: WSEvent) => void): void {
    const listeners = this.listeners.get(eventType)
    if (listeners) {
      listeners.delete(callback)
    }
  }

  private notifyListeners(event: WSEvent): void {
    // Notify type-specific listeners
    const typeListeners = this.listeners.get(event.type)
    if (typeListeners) {
      typeListeners.forEach((callback) => callback(event))
    }

    // Notify wildcard listeners
    const wildcardListeners = this.listeners.get('*')
    if (wildcardListeners) {
      wildcardListeners.forEach((callback) => callback(event))
    }
  }

  disconnect(): void {
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
    this.listeners.clear()
  }

  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN
  }
}
