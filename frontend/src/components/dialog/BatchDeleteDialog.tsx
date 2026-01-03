'use client'

import { X, AlertTriangle } from 'lucide-react'
import { apiClient } from '@/lib/api-client'
import { useState } from 'react'

interface BatchDeleteDialogProps {
  workflowIds: string[]
  workflowTitles: string[]
  onClose: () => void
  onSuccess?: () => void
}

export default function BatchDeleteDialog({
  workflowIds,
  workflowTitles,
  onClose,
  onSuccess,
}: BatchDeleteDialogProps) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleConfirmDelete = async () => {
    setLoading(true)
    setError(null)

    try {
      await apiClient.post('/workflows/batch-delete', {
        ids: workflowIds,
      })

      onSuccess?.()
      onClose()
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to delete workflows')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-lg p-6 max-w-md w-full mx-4">
        {/* Header */}
        <div className="flex items-center gap-3 mb-4">
          <AlertTriangle className="w-6 h-6 text-red-500" />
          <h2 className="text-lg font-semibold">Delete Workflows</h2>
        </div>

        {/* Message */}
        <p className="text-muted-foreground mb-4">
          Are you sure you want to delete {workflowIds.length} workflow
          {workflowIds.length > 1 ? 's' : ''}? This action cannot be undone.
        </p>

        {/* List of Workflows */}
        <div className="bg-muted/50 border border-border rounded-lg p-3 mb-4 max-h-48 overflow-y-auto">
          <ul className="space-y-2">
            {workflowTitles.map((title, idx) => (
              <li key={idx} className="text-sm text-muted-foreground flex items-start gap-2">
                <span className="text-xs mt-1">•</span>
                <span className="truncate">{title}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Error Message */}
        {error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-lg mb-4">
            <p className="text-sm text-red-700">{error}</p>
          </div>
        )}

        {/* Buttons */}
        <div className="flex gap-3 justify-end">
          <button
            onClick={onClose}
            disabled={loading}
            className="px-4 py-2 border border-border rounded-lg hover:bg-muted transition-colors disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            onClick={handleConfirmDelete}
            disabled={loading}
            className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors disabled:opacity-50"
          >
            {loading ? 'Deleting...' : 'Delete'}
          </button>
        </div>
      </div>
    </div>
  )
}
