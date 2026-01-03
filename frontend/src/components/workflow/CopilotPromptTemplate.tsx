/**
 * CopilotPromptTemplate Component
 *
 * 显示和编辑 LLM 提示模板
 */

import React, { useState } from 'react'
import { LLMPromptTemplate } from '@/types/copilot'
import { ChevronDown, Copy, Check, Edit2, Save, X } from 'lucide-react'

export interface CopilotPromptTemplateProps {
  template?: LLMPromptTemplate
  onApply?: (style: string) => void
  onApplyToNode?: (nodeId: string, style: string) => void
  loading?: boolean
  className?: string
}

/**
 * 提示模板组件
 *
 * 功能:
 * - 显示 LLM 提示模板预览
 * - 支持样式选择（结构化/详细/简洁）
 * - 显示令牌计数
 * - 支持编辑模式
 * - 支持复制到剪贴板
 * - 支持应用到节点
 */
export function CopilotPromptTemplate({
  template,
  onApply,
  onApplyToNode,
  loading = false,
  className,
}: CopilotPromptTemplateProps) {
  const [isExpanded, setIsExpanded] = useState(true)
  const [isEditing, setIsEditing] = useState(false)
  const [editedContent, setEditedContent] = useState(template?.content || '')
  const [selectedStyle, setSelectedStyle] = useState<'structured' | 'detailed' | 'concise'>(
    'structured'
  )
  const [copied, setCopied] = useState(false)

  if (!template) return null

  const estimateTokens = (text: string) => {
    // 粗略估计: 1 token ≈ 4 个字符
    return Math.ceil(text.length / 4)
  }

  const handleCopy = () => {
    navigator.clipboard.writeText(editedContent || template.content)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const handleSave = () => {
    setIsEditing(false)
    onApply?.(selectedStyle)
  }

  const handleApplyToNode = (nodeId: string) => {
    onApplyToNode?.(nodeId, selectedStyle)
  }

  return (
    <div className={`border-t bg-blue-50 ${className}`}>
      {/* 标题栏 */}
      <div
        className="flex items-center justify-between p-3 cursor-pointer hover:opacity-80 transition-opacity"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-blue-500" />
          <h4 className="font-semibold text-gray-900 text-sm">提示模板</h4>
          <span className="text-xs bg-blue-200 text-blue-700 px-2 py-0.5 rounded-full">
            {estimateTokens(editedContent || template.content)} tokens
          </span>
        </div>
        <ChevronDown
          className={`w-4 h-4 text-gray-500 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
        />
      </div>

      {/* 模板内容 */}
      {isExpanded && (
        <div className="space-y-3 p-3">
          {/* 样式选择器 */}
          <div className="flex gap-2">
            {[
              { value: 'structured' as const, label: '结构化' },
              { value: 'detailed' as const, label: '详细' },
              { value: 'concise' as const, label: '简洁' },
            ].map((style) => (
              <button
                key={style.value}
                onClick={() => {
                  setSelectedStyle(style.value)
                  setEditedContent(template.content)
                }}
                className={`text-xs px-3 py-1 rounded-lg font-semibold transition-all ${
                  selectedStyle === style.value
                    ? 'bg-blue-600 text-white shadow-sm'
                    : 'bg-white text-gray-700 border hover:border-blue-300'
                }`}
                disabled={loading}
              >
                {style.label}
              </button>
            ))}
          </div>

          {/* 编辑模式切换 */}
          <div className="flex items-center justify-between">
            <span className="text-xs text-gray-600 font-semibold">模板内容</span>
            <button
              onClick={() => {
                if (isEditing) {
                  handleSave()
                } else {
                  setIsEditing(true)
                }
              }}
              disabled={loading}
              className="text-xs text-blue-600 hover:text-blue-700 hover:underline disabled:opacity-50 flex items-center gap-1"
            >
              {isEditing ? (
                <>
                  <Save className="w-3 h-3" /> 保存
                </>
              ) : (
                <>
                  <Edit2 className="w-3 h-3" /> 编辑
                </>
              )}
            </button>
          </div>

          {/* 内容显示/编辑 */}
          {isEditing ? (
            <div className="space-y-2">
              <textarea
                value={editedContent}
                onChange={(e) => setEditedContent(e.target.value)}
                disabled={loading}
                className="w-full h-32 p-2 text-xs border rounded-lg font-mono resize-none disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <div className="flex gap-2 justify-end">
                <button
                  onClick={() => {
                    setIsEditing(false)
                    setEditedContent(template.content)
                  }}
                  disabled={loading}
                  className="text-xs px-2 py-1 border rounded-lg text-gray-700 hover:bg-gray-100 disabled:opacity-50 flex items-center gap-1"
                >
                  <X className="w-3 h-3" /> 取消
                </button>
                <button
                  onClick={handleSave}
                  disabled={loading}
                  className="text-xs px-3 py-1 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center gap-1"
                >
                  <Save className="w-3 h-3" /> 保存
                </button>
              </div>
            </div>
          ) : (
            <div className="bg-white rounded-lg p-2 border font-mono text-xs text-gray-700 max-h-40 overflow-y-auto whitespace-pre-wrap break-words">
              {editedContent || template.content}
            </div>
          )}

          {/* 操作按钮 */}
          <div className="flex gap-2">
            <button
              onClick={handleCopy}
              disabled={loading}
              className="flex-1 text-xs px-2 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 disabled:opacity-50 flex items-center justify-center gap-1 transition-all"
            >
              {copied ? (
                <>
                  <Check className="w-3 h-3 text-green-600" /> 已复制
                </>
              ) : (
                <>
                  <Copy className="w-3 h-3" /> 复制
                </>
              )}
            </button>
            <button
              onClick={() => onApply?.(selectedStyle)}
              disabled={loading}
              className="flex-1 text-xs px-2 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-all"
            >
              应用
            </button>
          </div>

          {/* 模板信息 */}
          <div className="text-xs text-gray-600 bg-gray-50 rounded-lg p-2 space-y-1">
            <p>
              <span className="font-semibold">版本:</span> {template.version}
            </p>
            {template.description && (
              <p>
                <span className="font-semibold">说明:</span> {template.description}
              </p>
            )}
            {template.examples && template.examples.length > 0 && (
              <div>
                <p className="font-semibold mb-1">示例:</p>
                <ul className="ml-3 space-y-0.5">
                  {template.examples.slice(0, 2).map((example, idx) => (
                    <li key={idx} className="text-gray-600">
                      • {example}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default CopilotPromptTemplate
