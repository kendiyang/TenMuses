"use client";

import { useState, useRef, useEffect } from 'react';
import { Play, Square, Trash2, CheckCircle, XCircle, Loader2 } from 'lucide-react';

interface ExecutionEvent {
  type: string;
  threadId?: string;
  nodeId?: string;
  payload?: any;
  timestamp: string;
}

export default function WebSocketTestPage() {
  const [isConnected, setIsConnected] = useState(false);
  const [isExecuting, setIsExecuting] = useState(false);
  const [threadId, setThreadId] = useState('');
  const [events, setEvents] = useState<ExecutionEvent[]>([]);
  const [output, setOutput] = useState('');
  const [error, setError] = useState<string | null>(null);
  
  const wsRef = useRef<WebSocket | null>(null);
  const eventsEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Auto-scroll to bottom of events
    eventsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [events]);

  const generateThreadId = () => {
    return `test-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  };

  const connectWebSocket = () => {
    const newThreadId = generateThreadId();
    setThreadId(newThreadId);
    setError(null);
    setEvents([]);
    setOutput('');

    const wsUrl = `ws://localhost:8000/api/v1/ws/run/${newThreadId}`;
    
    addEvent({
      type: 'system',
      payload: { message: `Connecting to ${wsUrl}` },
      timestamp: new Date().toISOString()
    });

    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      setIsConnected(true);
      addEvent({
        type: 'system',
        payload: { message: 'WebSocket connected' },
        timestamp: new Date().toISOString()
      });
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        addEvent({
          ...data,
          timestamp: new Date().toISOString()
        });

        // Handle specific event types
        if (data.type === 'token') {
          const content = data.payload?.content || '';
          setOutput(prev => prev + content);
        } else if (data.type === 'run_completed') {
          setIsExecuting(false);
        } else if (data.type === 'error') {
          setError(data.payload?.message || 'Unknown error');
          setIsExecuting(false);
        }
      } catch (err) {
        console.error('Failed to parse WebSocket message:', err);
      }
    };

    ws.onerror = (err) => {
      setError('WebSocket error occurred');
      addEvent({
        type: 'error',
        payload: { message: 'WebSocket error' },
        timestamp: new Date().toISOString()
      });
    };

    ws.onclose = () => {
      setIsConnected(false);
      setIsExecuting(false);
      addEvent({
        type: 'system',
        payload: { message: 'WebSocket disconnected' },
        timestamp: new Date().toISOString()
      });
    };

    wsRef.current = ws;
  };

  const startExecution = () => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      setError('WebSocket not connected');
      return;
    }

    setIsExecuting(true);
    setOutput('');
    setError(null);

    const startMessage = {
      action: 'start',
      input: 'Write a haiku about AI and machine learning'
    };

    wsRef.current.send(JSON.stringify(startMessage));
    
    addEvent({
      type: 'system',
      payload: { message: 'Sent start command', data: startMessage },
      timestamp: new Date().toISOString()
    });
  };

  const stopExecution = () => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      const stopMessage = {
        action: 'stop'
      };
      wsRef.current.send(JSON.stringify(stopMessage));
      setIsExecuting(false);
    }
  };

  const disconnect = () => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
  };

  const addEvent = (event: ExecutionEvent) => {
    setEvents(prev => [...prev, event]);
  };

  const clearEvents = () => {
    setEvents([]);
    setOutput('');
    setError(null);
  };

  const getEventColor = (type: string) => {
    switch (type) {
      case 'connected':
        return 'text-green-600 bg-green-50 border-green-200';
      case 'run_started':
        return 'text-blue-600 bg-blue-50 border-blue-200';
      case 'node_started':
      case 'node_status':
        return 'text-purple-600 bg-purple-50 border-purple-200';
      case 'token':
        return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 'run_completed':
        return 'text-green-600 bg-green-50 border-green-200';
      case 'error':
        return 'text-red-600 bg-red-50 border-red-200';
      case 'system':
        return 'text-gray-600 bg-gray-50 border-gray-200';
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">WebSocket Execution Test</h1>
          <p className="text-gray-600">Test workflow execution via WebSocket connection</p>
        </div>

        {/* Control Panel */}
        <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
          <div className="flex items-center gap-4 mb-4">
            <div className="flex items-center gap-2">
              <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
              <span className="text-sm font-medium">
                {isConnected ? 'Connected' : 'Disconnected'}
              </span>
            </div>
            {threadId && (
              <div className="text-sm text-gray-600">
                Thread ID: <span className="font-mono text-xs">{threadId}</span>
              </div>
            )}
          </div>

          <div className="flex gap-3">
            <button
              onClick={connectWebSocket}
              disabled={isConnected}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {isConnected ? <CheckCircle size={16} /> : <XCircle size={16} />}
              {isConnected ? 'Connected' : 'Connect'}
            </button>

            <button
              onClick={startExecution}
              disabled={!isConnected || isExecuting}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {isExecuting ? <Loader2 size={16} className="animate-spin" /> : <Play size={16} />}
              {isExecuting ? 'Executing...' : 'Start Execution'}
            </button>

            <button
              onClick={stopExecution}
              disabled={!isExecuting}
              className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center gap-2"
            >
              <Square size={16} />
              Stop
            </button>

            <button
              onClick={disconnect}
              disabled={!isConnected}
              className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Disconnect
            </button>

            <button
              onClick={clearEvents}
              className="ml-auto px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 flex items-center gap-2"
            >
              <Trash2 size={16} />
              Clear
            </button>
          </div>

          {error && (
            <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
              {error}
            </div>
          )}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Events Log */}
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h2 className="text-xl font-bold mb-4">Events Log</h2>
            <div className="h-[500px] overflow-y-auto space-y-2 font-mono text-xs">
              {events.length === 0 ? (
                <div className="text-gray-400 text-center py-8">No events yet. Connect and start execution.</div>
              ) : (
                events.map((event, index) => (
                  <div
                    key={index}
                    className={`p-3 rounded border ${getEventColor(event.type)}`}
                  >
                    <div className="flex items-start justify-between mb-1">
                      <span className="font-bold">{event.type}</span>
                      <span className="text-xs opacity-70">
                        {new Date(event.timestamp).toLocaleTimeString()}
                      </span>
                    </div>
                    {event.nodeId && (
                      <div className="text-xs opacity-80">Node: {event.nodeId}</div>
                    )}
                    {event.payload && (
                      <pre className="text-xs mt-1 overflow-x-auto">
                        {JSON.stringify(event.payload, null, 2)}
                      </pre>
                    )}
                  </div>
                ))
              )}
              <div ref={eventsEndRef} />
            </div>
          </div>

          {/* Output */}
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h2 className="text-xl font-bold mb-4">Execution Output</h2>
            <div className="h-[500px] overflow-y-auto bg-gray-900 text-green-400 p-4 rounded font-mono text-sm whitespace-pre-wrap">
              {output || 'No output yet...'}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
