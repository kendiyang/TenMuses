'use client'

import { useState } from 'react'
import { X, AlertCircle, CheckCircle, Copy, Clock, Zap } from 'lucide-react'
import { apiClient } from '@/lib/api-client'

interface ShareWorkflowDialogProps {
  workflowId: string
  workflowTitle: string
  onClose: () => void
  onSuccess?: () => void
}

type Permission = 'view' | 'edit' | 'execute'

const PERMISSION_LABELS: Record<Permission, string> = {
  view: 'View Only',
  edit: 'View & Edit',
  execute: 'Execute',
}

const PERMISSION_DESCRIPTIONS: Record<Permission, string> = {
  view: 'Recipients can only view the workflow',
  edit: 'Recipients can view and edit the workflow',
  execute: 'Recipients can execute and run the workflow',
}

export default function ShareWorkflowDialog({
  workflowId,
  workflowTitle,
  onClose,
  onSuccess,
}: ShareWorkflowDialogProps) {
  const [formData, setFormData] = useState({
    permission: 'view' as Permission,
    expiresIn: '30' as string, // days, '0' means no expiration
    maxUses: '0' as string, // 0 means unlimited
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [shareToken, setShareToken] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)

  const handlePermissionChange = (permission: Permission) => {
    setFormData((prev) => ({
      ...prev,
      permission,
    }))
  }

  const handleExpiresInChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setFormData((prev) => ({
      ...prev,
      expiresIn: e.target.value,
    }))
  }

  const handleMaxUsesChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData((prev) => ({
      ...prev,
      maxUses: e.target.value,
    }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    setLoading(true)
    setError(null)

    try {
      const expiresInDays = parseInt(formData.expiresIn, 10)
      const maxUses = parseInt(formData.maxUses, 10)

      const payload = {
        permission: formData.permission,
        expires_in_days: expiresInDays > 0 ? expiresInDays : null,
        max_uses: maxUses > 0 ? maxUses : null,
      }

      const response = await apiClient.post<{ share_token: string }>(
        `/workflows/${workflowId}/share`,
        payload
      )

      setShareToken(response.share_token)
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to create share link')
    } finally {
      setLoading(false)
    }
  }

  const shareUrl = shareToken
    ? `${typeof window !== 'undefined' ? window.location.origin : ''}/share/${shareToken}`
    : ''

  const handleCopyLink = () => {
    if (shareUrl) {
      navigator.clipboard.writeText(shareUrl)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  if (shareToken) {
    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg shadow-lg p-8 max-w-2xl w-full mx-4">
          {/* Success Header */}
          <div className="flex items-center gap-3 mb-6">
            <CheckCircle className="w-6 h-6 text-green-500" />
            <h3 className="text-lg font-semibold">Share Link Created</h3>
          </div>

          {/* Share Details */}
          <div className="space-y-4 mb-6">
            {/* Permission */}
            <div className="flex items-center gap-3 p-4 bg-muted/50 rounded-lg">
              <Zap className="w-5 h-5 text-primary flex-shrink-0" />
              <div>
                <p className="text-sm font-medium">Permission Level</p>
                <p className="text-xs text-muted-foreground">
                  {PERMISSION_DESCRIPTIONS[formData.permission as Permission]}
                </p>
              </div>
            </div>

            {/* Expiration */}
            {formData.expiresIn !== '0' && (
              <div className="flex items-center gap-3 p-4 bg-muted/50 rounded-lg">
                <Clock className="w-5 h-5 text-primary flex-shrink-0" />
                <div>
                  <p className="text-sm font-medium">Expires In</p>
                  <p className="text-xs text-muted-foreground">
                    {formData.expiresIn} days
                  </p>
                </div>
              </div>
            )}

            {/* Usage Limit */}
            {formData.maxUses !== '0' && (
              <div className="flex items-center gap-3 p-4 bg-muted/50 rounded-lg">
                <Zap className="w-5 h-5 text-primary flex-shrink-0" />
                <div>
                  <p className="text-sm font-medium">Usage Limit</p>
                  <p className="text-xs text-muted-foreground">
                    {formData.maxUses} uses
                  </p>
                </div>
              </div>
            )}
          </div>

          {/* Share Link */}
          <div className="mb-6">
            <label className="block text-sm font-medium mb-2">Share Link</label>
            <div className="flex gap-2">
              <input
                type="text"
                value={shareUrl}
                readOnly
                className="flex-1 px-3 py-2 border border-border rounded-lg bg-muted/50 text-sm"
              />
              <button
                onClick={handleCopyLink}
                className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:opacity-90 transition-opacity flex items-center gap-2 text-sm"
              >
                <Copy className="w-4 h-4" />
                {copied ? 'Copied!' : 'Copy'}
              </button>
            </div>
          </div>

          {/* Info */}
          <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg mb-6">
            <p className="text-sm text-blue-800">
              Share this link with others. They can access your workflow with the specified permissions.
            </p>
          </div>

          {/* Buttons */}
          <div className="flex gap-3 justify-end">
            <button
              onClick={onClose}
              className="px-4 py-2 border border-border rounded-lg hover:bg-muted transition-colors"
            >
              Done
            </button>
            <button
              onClick={() => {
                setShareToken(null)
                onSuccess?.()
              }}
              className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:opacity-90 transition-opacity"
            >
              Create Another Link
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-lg w-full max-w-2xl max-h-[90vh] overflow-y-auto mx-4">
        {/* Header */}
        <div className="sticky top-0 flex items-center justify-between p-6 border-b border-border bg-white">
          <h2 className="text-xl font-semibold">Share Workflow</h2>
          <button
            onClick={onClose}
            className="text-muted-foreground hover:text-foreground transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* Error Message */}
          {error && (
            <div className="flex gap-3 p-4 bg-red-50 border border-red-200 rounded-lg">
              <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-red-700">{error}</p>
            </div>
          )}

          {/* Permission Selection */}
          <div>
            <label className="block text-sm font-medium mb-4">
              Permission Level
            </label>
            <div className="space-y-3">
              {(Object.keys(PERMISSION_LABELS) as Permission[]).map((perm) => (
                <label
                  key={perm}
                  className="flex items-center gap-3 p-4 border border-border rounded-lg cursor-pointer hover:bg-muted/50 transition-colors"
                >
                  <input
                    type="radio"
                    name="permission"
                    value={perm}
                    checked={formData.permission === perm}
                    onChange={() => handlePermissionChange(perm)}
                    className="w-4 h-4"
                  />
                  <div className="flex-1">
                    <p className="text-sm font-medium">{PERMISSION_LABELS[perm]}</p>
                    <p className="text-xs text-muted-foreground">
                      {PERMISSION_DESCRIPTIONS[perm]}
                    </p>
                  </div>
                </label>
              ))}
            </div>
          </div>

          {/* Expiration */}
          <div>
            <label className="block text-sm font-medium mb-2">
              Link Expiration
            </label>
            <select
              value={formData.expiresIn}
              onChange={handleExpiresInChange}
              className="w-full px-3 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/50"
            >
              <option value="1">1 day</option>
              <option value="7">7 days</option>
              <option value="30">30 days</option>
              <option value="90">90 days</option>
              <option value="0">Never expires</option>
            </select>
            <p className="text-xs text-muted-foreground mt-1">
              The share link will automatically expire after this period
            </p>
          </div>

          {/* Usage Limit */}
          <div>
            <label className="block text-sm font-medium mb-2">
              Usage Limit (Optional)
            </label>
            <input
              type="number"
              value={formData.maxUses}
              onChange={handleMaxUsesChange}
              min="0"
              placeholder="0 = unlimited"
              className="w-full px-3 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/50"
            />
            <p className="text-xs text-muted-foreground mt-1">
              Leave at 0 to allow unlimited access. Set to a number to limit how many times the link can be used.
            </p>
          </div>

          {/* Info Box */}
          <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <p className="text-sm text-blue-800">
              ℹ️ Recipients will need to sign in to access shared workflows. The link permissions apply to all users who access it.
            </p>
          </div>

          {/* Buttons */}
          <div className="flex gap-3 justify-end pt-4 border-t border-border">
            <button
              type="button"
              onClick={onClose}
              disabled={loading}
              className="px-4 py-2 border border-border rounded-lg hover:bg-muted transition-colors disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:opacity-90 transition-opacity disabled:opacity-50"
            >
              {loading ? 'Creating Link...' : 'Create Share Link'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
