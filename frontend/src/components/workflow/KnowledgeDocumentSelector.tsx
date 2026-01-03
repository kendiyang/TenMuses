'use client'

import { useState, useEffect } from 'react'
import { apiClient } from '@/lib/api-client'
import { Search, FileText, X } from 'lucide-react'

export interface KnowledgeDocument {
  id: string
  title: string
  sourceType: 'file' | 'url' | 'text'
  createdAt: string
}

interface KnowledgeDocumentSelectorProps {
  selectedDocumentIds: string[]
  onChange: (documentIds: string[]) => void
}

export default function KnowledgeDocumentSelector({
  selectedDocumentIds,
  onChange,
}: KnowledgeDocumentSelectorProps) {
  const [documents, setDocuments] = useState<KnowledgeDocument[]>([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadDocuments()
  }, [])

  const loadDocuments = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await apiClient.get<{ documents: KnowledgeDocument[] }>('/kb/documents')
      setDocuments(data.documents || [])
    } catch (err) {
      console.error('Failed to load knowledge documents:', err)
      setError('Failed to load documents')
    } finally {
      setLoading(false)
    }
  }

  const filteredDocuments = documents.filter((doc) =>
    doc.title.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const selectedDocuments = documents.filter((doc) =>
    selectedDocumentIds.includes(doc.id)
  )

  const handleToggleDocument = (docId: string) => {
    if (selectedDocumentIds.includes(docId)) {
      onChange(selectedDocumentIds.filter((id) => id !== docId))
    } else {
      onChange([...selectedDocumentIds, docId])
    }
  }

  const handleRemoveDocument = (docId: string) => {
    onChange(selectedDocumentIds.filter((id) => id !== docId))
  }

  if (loading) {
    return (
      <div className="text-sm text-muted-foreground py-4 text-center">
        Loading documents...
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-sm text-red-600 py-4">
        {error}
        <button
          onClick={loadDocuments}
          className="ml-2 text-blue-600 hover:underline"
        >
          Retry
        </button>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {/* Selected Documents */}
      {selectedDocuments.length > 0 && (
        <div className="space-y-2">
          <div className="text-xs font-medium text-muted-foreground">
            Selected Documents ({selectedDocuments.length})
          </div>
          <div className="flex flex-wrap gap-2">
            {selectedDocuments.map((doc) => (
              <div
                key={doc.id}
                className="flex items-center gap-1 px-2 py-1 bg-blue-50 text-blue-700 rounded-md text-xs"
              >
                <FileText className="w-3 h-3" />
                <span>{doc.title}</span>
                <button
                  onClick={() => handleRemoveDocument(doc.id)}
                  className="ml-1 hover:bg-blue-100 rounded p-0.5"
                >
                  <X className="w-3 h-3" />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search documents..."
          className="w-full pl-9 pr-3 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary text-sm"
        />
      </div>

      {/* Document List */}
      <div className="border border-border rounded-lg max-h-48 overflow-y-auto">
        {filteredDocuments.length === 0 ? (
          <div className="p-4 text-center text-sm text-muted-foreground">
            {documents.length === 0
              ? 'No documents available. Upload documents first.'
              : 'No documents match your search.'}
          </div>
        ) : (
          <div className="divide-y divide-border">
            {filteredDocuments.map((doc) => {
              const isSelected = selectedDocumentIds.includes(doc.id)
              return (
                <label
                  key={doc.id}
                  className="flex items-center gap-3 p-3 hover:bg-muted cursor-pointer"
                >
                  <input
                    type="checkbox"
                    checked={isSelected}
                    onChange={() => handleToggleDocument(doc.id)}
                    className="w-4 h-4 rounded border-gray-300 text-primary focus:ring-primary"
                  />
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium truncate">{doc.title}</div>
                    <div className="text-xs text-muted-foreground">
                      {doc.sourceType} • {new Date(doc.createdAt).toLocaleDateString()}
                    </div>
                  </div>
                </label>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
