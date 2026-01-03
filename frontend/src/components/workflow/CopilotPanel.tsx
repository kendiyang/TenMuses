/**
 * CopilotPanel
 *
 * Copilot AI 助手面板，支持对话和流式响应两种模式
 */

import React, { useState, useRef, useEffect } from 'react'
import { useCopilotChat } from '@/hooks/useCopilotChat'
import { useCopilotStream } from '@/hooks/useCopilotStream'
import { useWorkflowContext } from '@/hooks/useWorkflowContext'
import { useSuggestionStorage } from '@/lib/suggestion-storage'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { getAvailableLLMConfigs, LLMConfig } from '@/services/llm-config-client'
import { CopilotSuggestions } from '@/components/workflow/CopilotSuggestions'
import { CopilotDiagnostics } from '@/components/workflow/CopilotDiagnostics'
import { CopilotPromptTemplate } from '@/components/workflow/CopilotPromptTemplate'
import { CopilotStreamDisplay } from '@/components/workflow/CopilotStreamDisplay'
import { CopilotHistory } from '@/components/workflow/CopilotHistory'
import { TemplateEditorWithPreview } from '@/components/workflow/TemplatePreview'
import { ContextManagerComponent } from '@/components/workflow/ContextManager'
import { createSystemContext, VariableContext } from '@/lib/template-engine'
import {
  Sparkles,
  Send,
  RefreshCw,
  Copy,
  Trash2,
  Settings,
  ChevronDown,
  AlertCircle,
  Lightbulb,
  Search,
  Zap,
  Clock,
  FileText,
  Sliders,
  Paperclip,
} from 'lucide-react'
import { cn } from '@/lib/utils'

export interface CopilotPanelProps {
  workflowId?: string
  onNodeApply?: (node: any) => void
  onWorkflowApply?: (workflow: any) => void
  className?: string
}

export function CopilotPanel({
  workflowId,
  onNodeApply,
  onWorkflowApply,
  className,
}: CopilotPanelProps) {
  // 对话模式 Hook
  const { messages, isLoading, error, sendMessage, clearHistory } = useCopilotChat({
    onError: (err) => {
      console.error('Copilot error:', err)
    },
  })

  // 流式模式 Hook
  const {
    currentMessage,
    isLoading: streamLoading,
    error: streamError,
    streamChat,
    streamWorkflowSuggestions,
    streamWorkflowDiagnosis,
    cancel: cancelStream,
    reset: resetStream,
  } = useCopilotStream({
    onMessageUpdate: (content) => {
      // 可选：更新消息
    },
    onError: (err) => {
      console.error('Stream error:', err)
    },
  })

  const { getContext } = useWorkflowContext()

  const [inputValue, setInputValue] = useState('')
  const [isExpanded, setIsExpanded] = useState(true)
  const [activeTab, setActiveTab] = useState<'chat' | 'stream' | 'history' | 'template' | 'context'>('chat')
  const [agentMode, setAgentMode] = useState<'agent' | 'ask'>('agent')
  const [modelChoice, setModelChoice] = useState<string>('auto')
  const [showAgentMenu, setShowAgentMenu] = useState(false)
  const [showModelMenu, setShowModelMenu] = useState(false)
  const [llmOptions, setLlmOptions] = useState<LLMConfig[]>([])
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // 模板状态
  const [template, setTemplate] = useState('请为 {{workflowName}} 工作流建议一个 {{feature}} 功能。\n\n要求：\n- {{requirement1}}\n- {{requirement2}}')
  const [templateContext, setTemplateContext] = useState<VariableContext>(createSystemContext({
    workflowName: '我的工作流',
    feature: 'RAG 搜索',
    requirement1: '支持向量搜索',
    requirement2: '结果可排序'
  }))

  const storage = useSuggestionStorage()

  // 拉取可用 LLM 配置
  useEffect(() => {
    getAvailableLLMConfigs().then((configs) => setLlmOptions(configs))
  }, [])

  // 自动滚动到最新消息
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = async () => {
    if (!inputValue.trim() || isLoading) return

    // 获取工作流上下文
    const workflowContext = getContext()

    await sendMessage(inputValue, {
      workflow_id: workflowId,
      context_type: 'workflow_editor',
      agent_mode: agentMode,
      model: modelChoice,
      workflow: {
        nodes: workflowContext.nodes,
        edges: workflowContext.edges,
        nodeCount: workflowContext.nodeCount,
        edgeCount: workflowContext.edgeCount,
      },
    })

    setInputValue('')
  }

  const handleQuickButton = (text: string) => {
    setInputValue(text)
  }

  const handleStreamQuickAction = async (type: 'suggest' | 'diagnose') => {
    const context = getContext()
    try {
      if (type === 'suggest') {
        await streamWorkflowSuggestions('建议改进当前工作流')
      } else if (type === 'diagnose') {
        await streamWorkflowDiagnosis(context.nodes || [], context.edges || [])
      }
    } catch (err) {
      console.error('Quick action failed:', err)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const quickButtons = [
    {
      icon: Lightbulb,
      text: '建议一个完整的工作流',
      label: '💡 建议工作流',
    },
    {
      icon: Search,
      text: '检查这个工作流是否正确',
      label: '🔍 诊断工作流',
    },
    {
      icon: Zap,
      text: '帮我生成一个 LLM 提示词',
      label: '✍️ 生成提示词',
    },
  ]

  return (
    <div className={cn('flex flex-col h-full', className)}>
      {/* 标题栏 */}
      <div className="flex items-center justify-between p-3 border-b bg-gradient-to-r from-purple-50 to-blue-50 rounded-t-lg">
        <div className="flex items-center gap-2">
          <Sparkles className="h-5 w-5 text-purple-600" />
          <h3 className="font-semibold text-gray-900 text-sm">Copilot 助手</h3>
        </div>
        <div className="flex items-center gap-2">
          {/* 标签页选择器 */}
          <div className="flex gap-1 bg-white rounded-lg p-1">
            <button
              onClick={() => setActiveTab('chat')}
              className={cn(
                'px-2 py-1 text-xs font-medium rounded transition-colors',
                activeTab === 'chat'
                  ? 'bg-purple-100 text-purple-700'
                  : 'text-gray-600 hover:text-gray-900'
              )}
            >
              对话
            </button>
            <button
              onClick={() => setActiveTab('stream')}
              className={cn(
                'px-2 py-1 text-xs font-medium rounded transition-colors flex items-center gap-1',
                activeTab === 'stream'
                  ? 'bg-blue-100 text-blue-700'
                  : 'text-gray-600 hover:text-gray-900'
              )}
            >
              <Zap className="h-3 w-3" />
              流式
            </button>
            <button
              onClick={() => setActiveTab('history')}
              className={cn(
                'px-2 py-1 text-xs font-medium rounded transition-colors flex items-center gap-1',
                activeTab === 'history'
                  ? 'bg-orange-100 text-orange-700'
                  : 'text-gray-600 hover:text-gray-900'
              )}
            >
              <Clock className="h-3 w-3" />
              历史
            </button>
            <button
              onClick={() => setActiveTab('template')}
              className={cn(
                'px-2 py-1 text-xs font-medium rounded transition-colors flex items-center gap-1',
                activeTab === 'template'
                  ? 'bg-green-100 text-green-700'
                  : 'text-gray-600 hover:text-gray-900'
              )}
            >
              <FileText className="h-3 w-3" />
              模板
            </button>
            <button
              onClick={() => setActiveTab('context')}
              className={cn(
                'px-2 py-1 text-xs font-medium rounded transition-colors flex items-center gap-1',
                activeTab === 'context'
                  ? 'bg-purple-100 text-purple-700'
                  : 'text-gray-600 hover:text-gray-900'
              )}
            >
              <Sliders className="h-3 w-3" />
              上下文
            </button>
          </div>

          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="text-gray-500 hover:text-gray-700"
          >
            <ChevronDown
              className={cn('h-4 w-4 transition-transform', isExpanded && 'rotate-180')}
            />
          </button>
        </div>
      </div>

      {/* 主内容 */}
      {isExpanded && (
        <div className="flex flex-col flex-1 min-h-0">
          {/* 聊天标签页 */}
          {activeTab === 'chat' && (
            <div className="flex flex-col flex-1 min-h-0">
              {/* 消息区域 */}
              <div className="flex-1 overflow-auto space-y-3 p-4 bg-white">
                {messages.length === 0 ? (
                  <div className="flex flex-col items-center justify-center h-full text-center">
                    <Sparkles className="h-12 w-12 text-purple-200 mb-3" />
                    <p className="text-sm text-gray-500 mb-4">开始对话以获得工作流建议</p>
                    <div className="space-y-2 w-full">
                      {quickButtons.map((btn) => (
                        <button
                          key={btn.text}
                          onClick={() => handleQuickButton(btn.text)}
                          className="w-full text-left px-3 py-2 rounded-lg text-xs text-gray-700 hover:bg-purple-50 transition-colors"
                        >
                          {btn.label}
                        </button>
                      ))}
                    </div>
                  </div>
                ) : (
                  <>
                    {messages.map((msg, idx) => (
                      <div key={idx} className="space-y-2">
                        <div
                          className={cn(
                            'flex gap-2',
                            msg.role === 'user' ? 'justify-end' : 'justify-start'
                          )}
                        >
                          {msg.role === 'assistant' && (
                            <div className="flex-shrink-0 w-6 h-6 rounded-full bg-purple-100 flex items-center justify-center mt-1">
                              <Sparkles className="h-4 w-4 text-purple-600" />
                            </div>
                          )}

                          <div
                            className={cn(
                              'max-w-xs px-3 py-2 rounded-lg text-sm break-words',
                              msg.role === 'user'
                                ? 'bg-purple-600 text-white'
                                : 'bg-gray-100 text-gray-900 border border-gray-200'
                            )}
                          >
                            <p className="whitespace-pre-wrap">{msg.content}</p>

                            {msg.role === 'assistant' && (
                              <div className="flex gap-1 mt-2">
                                <button
                                  onClick={() => {
                                    navigator.clipboard.writeText(msg.content)
                                  }}
                                  className="text-xs text-gray-600 hover:text-gray-900 flex items-center gap-1"
                                  title="复制"
                                >
                                  <Copy className="h-3 w-3" />
                                </button>
                              </div>
                            )}
                          </div>
                        </div>

                        {/* 使用提取的建议组件 */}
                        {msg.suggestions && msg.role === 'assistant' && (
                          <div className="ml-8">
                            <CopilotSuggestions
                              suggestions={[
                                ...(msg.suggestions.workflows?.map((wf: any, idx: number) => ({
                                  type: 'workflow' as const,
                                  id: wf.id || `wf_${idx}`,
                                  name: wf.name,
                                  description: wf.description,
                                  nodeCount: wf.nodes?.length || 0,
                                  edgeCount: wf.edges?.length || 0,
                                  data: wf,
                                })) || []),
                                ...(msg.suggestions.nodes?.map((node: any, idx: number) => ({
                                  type: 'node' as const,
                                  id: node.id || `node_${idx}`,
                                  nodeType: node.type,
                                  label: node.label || node.type,
                                  explanation: node.explanation,
                                  data: node,
                                })) || []),
                              ]}
                              onApply={(suggestion: any) => {
                                if (suggestion.type === 'workflow') {
                                  onWorkflowApply?.(suggestion.data)
                                } else {
                                  onNodeApply?.(suggestion.data)
                                }
                              }}
                              loading={isLoading}
                            />
                          </div>
                        )}

                        {/* 使用提取的诊断组件 */}
                        {msg.diagnostics && msg.role === 'assistant' && (
                          <div className="ml-8">
                            <CopilotDiagnostics
                              result={msg.diagnostics}
                              onHighlightNode={(nodeId: string) => {
                                console.log('Highlighting node:', nodeId)
                              }}
                            />
                          </div>
                        )}

                        {/* 使用提取的提示模板组件 */}
                        {msg.template && msg.role === 'assistant' && (
                          <div className="ml-8">
                            <CopilotPromptTemplate
                              template={msg.template}
                              onApply={(style: string) => {
                                console.log('Applied template with style:', style)
                              }}
                              loading={isLoading}
                            />
                          </div>
                        )}
                      </div>
                    ))}

                    {isLoading && (
                      <div className="flex justify-start gap-2">
                        <div className="flex-shrink-0 w-6 h-6 rounded-full bg-purple-100 flex items-center justify-center">
                          <Sparkles className="h-4 w-4 text-purple-600" />
                        </div>
                        <div className="bg-gray-100 px-3 py-2 rounded-lg">
                          <div className="flex gap-1">
                            <div className="h-2 w-2 bg-gray-400 rounded-full animate-bounce" />
                            <div className="h-2 w-2 bg-gray-400 rounded-full animate-bounce delay-100" />
                            <div className="h-2 w-2 bg-gray-400 rounded-full animate-bounce delay-200" />
                          </div>
                        </div>
                      </div>
                    )}

                    {error && (
                      <div className="flex justify-start gap-2">
                        <AlertCircle className="h-5 w-5 text-red-500 flex-shrink-0 mt-1" />
                        <div className="bg-red-50 text-red-700 px-3 py-2 rounded-lg text-xs border border-red-200">
                          {error.message}
                        </div>
                      </div>
                    )}

                    <div ref={messagesEndRef} />
                  </>
                )}
              </div>

              {/* 快速按钮 */}
              {messages.length > 0 && (
                <div className="border-t p-2 bg-gray-50 space-y-1">
                  {quickButtons.map((btn) => (
                    <button
                      key={btn.text}
                      onClick={() => handleQuickButton(btn.text)}
                      className="w-full text-left px-3 py-1.5 rounded text-xs text-gray-700 hover:bg-white transition-colors flex items-center gap-2"
                    >
                      <span className="text-base">{btn.label.split(' ')[0]}</span>
                      <span className="text-gray-600">{btn.label.slice(2)}</span>
                    </button>
                  ))}
                </div>
              )}

              {/* 输入框 */}
              <div className="border-t bg-white rounded-b-lg space-y-3 p-3">
                <div className="flex items-start gap-2">
                  <div className="flex items-start gap-2 flex-1 rounded-2xl border border-gray-200 bg-gray-50 px-3 py-2 focus-within:border-purple-400 focus-within:ring-2 focus-within:ring-purple-100">
                    <button
                      type="button"
                      className="text-gray-500 hover:text-gray-800 transition-colors"
                    >
                      <Paperclip className="h-4 w-4" />
                    </button>
                    <textarea
                      placeholder="Describe what to build next"
                      value={inputValue}
                      onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setInputValue(e.target.value)}
                      onKeyDown={handleKeyDown}
                      disabled={isLoading}
                      rows={3}
                      className="flex-1 border-0 bg-transparent px-0 text-sm shadow-none focus:outline-none resize-none"
                    />
                  </div>
                </div>

                <div className="flex items-center justify-between text-xs text-gray-600 gap-3">
                  <div className="flex items-center gap-2">
                    <div className="relative">
                      <button
                        type="button"
                        onClick={() => setShowAgentMenu((v) => !v)}
                        className="inline-flex items-center gap-1 rounded-full border border-gray-200 bg-gray-50 px-2.5 py-1 hover:border-purple-300 hover:text-foreground transition-colors"
                      >
                        {agentMode === 'agent' ? 'Agent' : 'Ask'}
                        <ChevronDown className="h-3 w-3" />
                      </button>
                      {showAgentMenu && (
                        <div className="absolute left-0 top-full mt-1 w-28 rounded-lg border border-gray-200 bg-white shadow-lg z-30">
                          {[
                            { label: 'Agent', value: 'agent' },
                            { label: 'Ask', value: 'ask' },
                          ].map((item) => (
                            <button
                              key={item.value}
                              onClick={() => {
                                setAgentMode(item.value as 'agent' | 'ask')
                                setShowAgentMenu(false)
                              }}
                              className={`w-full text-left px-3 py-2 hover:bg-purple-50 ${agentMode === item.value ? 'text-purple-600 font-semibold' : 'text-gray-700'}`}
                            >
                              {item.label}
                            </button>
                          ))}
                        </div>
                      )}
                    </div>

                    <div className="relative">
                      <button
                        type="button"
                        onClick={() => setShowModelMenu((v) => !v)}
                        className="inline-flex items-center gap-1 rounded-full border border-gray-200 bg-gray-50 px-2.5 py-1 hover:border-purple-300 hover:text-foreground transition-colors"
                      >
                        {modelChoice === 'auto'
                          ? 'Auto'
                          : llmOptions.find((o) => o.model_name === modelChoice)?.display_name || modelChoice}
                        <ChevronDown className="h-3 w-3" />
                      </button>
                      {showModelMenu && (
                        <div className="absolute left-0 top-full mt-1 w-56 rounded-lg border border-gray-200 bg-white shadow-lg z-30 max-h-60 overflow-auto">
                          <button
                            onClick={() => {
                              setModelChoice('auto')
                              setShowModelMenu(false)
                            }}
                            className={`w-full text-left px-3 py-2 hover:bg-purple-50 ${modelChoice === 'auto' ? 'text-purple-600 font-semibold' : 'text-gray-700'}`}
                          >
                            Auto（系统自动选择）
                          </button>
                          {llmOptions.map((item) => (
                            <button
                              key={item.id}
                              onClick={() => {
                                setModelChoice(item.model_name)
                                setShowModelMenu(false)
                              }}
                              className={`w-full text-left px-3 py-2 hover:bg-purple-50 ${modelChoice === item.model_name ? 'text-purple-600 font-semibold' : 'text-gray-700'}`}
                            >
                              {item.display_name}
                            </button>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      className="inline-flex h-8 w-8 items-center justify-center rounded-full border border-gray-200 text-gray-600 hover:text-foreground hover:border-purple-300 hover:bg-purple-50 transition-colors"
                      title="设置"
                    >
                      <Sliders className="h-4 w-4" />
                    </button>
                    <Button
                      type="button"
                      onClick={handleSend}
                      disabled={!inputValue.trim() || isLoading}
                      size="icon"
                      className="h-10 w-10 rounded-full bg-purple-600 hover:bg-purple-700"
                    >
                      <Send className="h-4 w-4" />
                    </Button>
                  </div>
                </div>

                {messages.length > 0 && (
                  <Button
                    variant="outline"
                    size="sm"
                    className="w-full text-xs"
                    onClick={clearHistory}
                  >
                    <Trash2 className="h-3 w-3 mr-1" />
                    清除历史
                  </Button>
                )}
              </div>
            </div>
          )}

          {/* 流式标签页 */}
          {activeTab === 'stream' && (
            <div className="flex flex-col flex-1 min-h-0">
              {/* 流式内容显示 */}
              <div className="flex-1 overflow-auto p-4 bg-white">
                <CopilotStreamDisplay
                  content={currentMessage}
                  isLoading={streamLoading}
                  error={streamError}
                  onCancel={cancelStream}
                />
              </div>

              {/* 快速操作 */}
              <div className="border-t p-3 bg-gray-50 space-y-2">
                <p className="text-xs font-semibold text-gray-700">快速操作</p>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    onClick={() => handleStreamQuickAction('suggest')}
                    disabled={streamLoading}
                    className={cn(
                      'px-3 py-2 rounded text-xs font-medium transition-colors',
                      streamLoading
                        ? 'bg-gray-200 text-gray-400'
                        : 'bg-blue-100 text-blue-700 hover:bg-blue-200'
                    )}
                  >
                    💡 建议改进
                  </button>
                  <button
                    onClick={() => handleStreamQuickAction('diagnose')}
                    disabled={streamLoading}
                    className={cn(
                      'px-3 py-2 rounded text-xs font-medium transition-colors',
                      streamLoading
                        ? 'bg-gray-200 text-gray-400'
                        : 'bg-green-100 text-green-700 hover:bg-green-200'
                    )}
                  >
                    🔍 流式诊断
                  </button>
                </div>
              </div>

              {/* 控制按钮 */}
              <div className="border-t p-3 bg-white rounded-b-lg">
                <Button
                  variant="outline"
                  size="sm"
                  className="w-full text-xs"
                  onClick={resetStream}
                >
                  <RefreshCw className="h-3 w-3 mr-1" />
                  清除响应
                </Button>
              </div>
            </div>
          )}

          {/* 历史标签页 */}
          {activeTab === 'history' && (
            <CopilotHistory
              onSelectSuggestion={(suggestion) => {
                console.log('Selected suggestion:', suggestion)
              }}
              onApply={(suggestion) => {
                if (suggestion.type === 'workflow') {
                  onWorkflowApply?.(suggestion.content)
                } else {
                  onNodeApply?.(suggestion.content)
                }
              }}
              className="flex-1"
            />
          )}

          {/* 模板标签页 */}
          {activeTab === 'template' && (
            <div className="flex-1 p-4 overflow-auto">
              <TemplateEditorWithPreview
                template={template}
                onTemplateChange={setTemplate}
                context={templateContext}
                onContextChange={setTemplateContext}
                onSend={(content) => {
                  // 将渲染后的内容发送到聊天
                  setInputValue(content)
                  setActiveTab('chat')
                }}
                className="h-full"
              />
            </div>
          )}

          {/* 上下文标签页 */}
          {activeTab === 'context' && (
            <div className="flex-1 p-4 overflow-auto">
              <ContextManagerComponent
                nodes={getContext().nodes || []}
                edges={getContext().edges || []}
                metadata={{
                  workflowId,
                  nodeCount: getContext().nodeCount || 0,
                  edgeCount: getContext().edgeCount || 0
                }}
                onContextChange={(context) => {
                  // 上下文变化时的回调，可以用于更新全局状态
                  console.log('Context updated:', context)
                }}
                layout="horizontal"
                className="h-full"
              />
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default CopilotPanel
