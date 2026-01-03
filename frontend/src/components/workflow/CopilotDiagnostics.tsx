/**
 * CopilotDiagnostics Component
 *
 * 显示 Copilot 对工作流的诊断结果
 */

import React, { useState } from 'react'
import { WorkflowDiagnosis } from '@/types/copilot'
import { AlertCircle, AlertTriangle, Info, CheckCircle, ChevronDown } from 'lucide-react'

export interface CopilotDiagnosticsProps {
  result?: WorkflowDiagnosis
  onHighlightNode?: (nodeId: string) => void
  className?: string
}

/**
 * 诊断结果组件
 * 
 * 功能:
 * - 显示工作流评分进度条
 * - 显示诊断摘要
 * - 列出所有问题和建议
 * - 支持节点定位功能
 * - 支持展开/折叠
 */
export function CopilotDiagnostics({
  result,
  onHighlightNode,
  className,
}: CopilotDiagnosticsProps) {
  const [isExpanded, setIsExpanded] = useState(true)

  if (!result) return null

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'from-green-400 to-green-500'
    if (score >= 60) return 'from-yellow-400 to-yellow-500'
    return 'from-red-400 to-red-500'
  }

  const getScoreBgColor = (score: number) => {
    if (score >= 80) return 'bg-green-50'
    if (score >= 60) return 'bg-yellow-50'
    return 'bg-red-50'
  }

  const getDiagnosticIcon = (level: string) => {
    switch (level) {
      case 'error':
        return <AlertCircle className="w-4 h-4 text-red-600 flex-shrink-0" />
      case 'warning':
        return <AlertTriangle className="w-4 h-4 text-yellow-600 flex-shrink-0" />
      default:
        return <Info className="w-4 h-4 text-blue-600 flex-shrink-0" />
    }
  }

  const getDiagnosticBgColor = (level: string) => {
    switch (level) {
      case 'error':
        return 'bg-red-50 border-red-200'
      case 'warning':
        return 'bg-yellow-50 border-yellow-200'
      default:
        return 'bg-blue-50 border-blue-200'
    }
  }

  const hasIssues = result.diagnostics && result.diagnostics.length > 0

  return (
    <div className={`border-t ${getScoreBgColor(result.score)} ${className}`}>
      {/* 标题栏 */}
      <div
        className="flex items-center justify-between p-3 cursor-pointer hover:opacity-80 transition-opacity"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center gap-2">
          {result.score >= 80 ? (
            <CheckCircle className="w-4 h-4 text-green-600" />
          ) : result.score >= 60 ? (
            <AlertTriangle className="w-4 h-4 text-yellow-600" />
          ) : (
            <AlertCircle className="w-4 h-4 text-red-600" />
          )}
          <h4 className="font-semibold text-gray-900 text-sm">诊断结果</h4>
        </div>
        <ChevronDown
          className={`w-4 h-4 text-gray-500 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
        />
      </div>

      {/* 诊断内容 */}
      {isExpanded && (
        <div className="space-y-3 p-3">
          {/* 评分卡片 */}
          <div className="bg-white rounded-lg p-3 border">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold text-gray-700">工作流评分</span>
              <span className="text-lg font-bold text-gray-900">{result.score}/100</span>
            </div>
            <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
              <div
                className={`h-full transition-all bg-gradient-to-r ${getScoreColor(result.score)}`}
                style={{ width: `${result.score}%` }}
              />
            </div>
          </div>

          {/* 摘要 */}
          <p className="text-xs text-gray-700 line-clamp-3 bg-white rounded-lg p-2 border">
            {result.summary}
          </p>

          {/* 诊断项目 */}
          {hasIssues ? (
            <div className="space-y-2">
              {result.diagnostics.map((diagnostic, idx) => (
                <div
                  key={idx}
                  className={`p-2 rounded-lg border ${getDiagnosticBgColor(diagnostic.level)}`}
                >
                  <div className="flex gap-2">
                    {getDiagnosticIcon(diagnostic.level)}
                    <div className="flex-1 min-w-0">
                      <h5 className="text-xs font-semibold text-gray-900 leading-tight">
                        {diagnostic.description}
                      </h5>
                      <p className="text-xs text-gray-700 mt-1">💡 {diagnostic.suggestion}</p>
                      {diagnostic.location?.node_id && (
                        <button
                          onClick={() => onHighlightNode?.(diagnostic.location!.node_id)}
                          className="text-xs text-blue-600 hover:text-blue-700 hover:underline mt-1 inline-flex items-center gap-1"
                        >
                          📍 查看节点
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="flex items-center gap-2 p-2 bg-green-100 rounded-lg border border-green-300">
              <CheckCircle className="w-4 h-4 text-green-600 flex-shrink-0" />
              <span className="text-xs text-green-700 font-semibold">工作流没有明显问题! ✨</span>
            </div>
          )}

          {/* 优化建议 */}
          {result.score < 90 && hasIssues && (
            <div className="text-xs text-gray-600 bg-gray-100 rounded-lg p-2">
              <p className="font-semibold mb-1">💡 优化建议:</p>
              <ul className="space-y-1 ml-4 list-disc">
                {result.diagnostics.slice(0, 2).map((d, idx) => (
                  <li key={idx}>{d.suggestion}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default CopilotDiagnostics
