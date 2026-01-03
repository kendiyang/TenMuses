/**
 * Knowledge Base Management Page
 * 路径: frontend/src/app/knowledge-base/page.tsx
 * 
 * 主页面：组织知识库文档管理、搜索、RAG 配置
 */

'use client'

import React, { useState, useEffect } from 'react'
import { Card } from '@/components/ui/card'
import DocumentsList from '@/components/knowledge/DocumentsList'
import UploadSection from '@/components/knowledge/UploadSection'
import SearchSection from '@/components/knowledge/SearchSection'
import DocumentDetail from '@/components/knowledge/DocumentDetail'
import SearchResults from '@/components/knowledge/SearchResults'
import { DocumentSelector } from '@/components/knowledge/DocumentSelector'

export default function KnowledgeBasePage() {
  const [selectedDocId, setSelectedDocId] = useState<string | null>(null)
  const [documents, setDocuments] = useState<any[]>([])
  const [isLoadingDocs, setIsLoadingDocs] = useState(true)
  const [searchResults, setSearchResults] = useState(null)
  const [isSearching, setIsSearching] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // 加载文档列表
  useEffect(() => {
    loadDocuments()
  }, [])

  const loadDocuments = async () => {
    try {
      setIsLoadingDocs(true)
      const response = await fetch('/api/v1/kb/documents', {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('accessToken')}`,
        },
      })

      if (!response.ok) throw new Error('Failed to load documents')

      const data = await response.json()
      setDocuments(data.data || [])
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load documents')
      console.error('Load documents error:', err)
    } finally {
      setIsLoadingDocs(false)
    }
  }

  const handleDocumentUploaded = (newDoc: any) => {
    setDocuments([newDoc, ...documents])
    setSelectedDocId(newDoc.id)
  }

  const handleDocumentDeleted = (docId: string) => {
    setDocuments(documents.filter((doc: any) => doc.id !== docId))
    if (selectedDocId === docId) {
      setSelectedDocId(null)
    }
  }

  const handleSearch = async (query: string, searchMode: 'document' | 'chunk', topK: number, minScore: number) => {
    try {
      setIsSearching(true)
      const response = await fetch('/api/v1/kb/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('accessToken')}`,
        },
        body: JSON.stringify({
          query,
          top_k: topK,
          min_score: minScore,
          search_chunks: searchMode === 'chunk',
        }),
      })

      if (!response.ok) throw new Error('Search failed')

      const data = await response.json()
      setSearchResults(data)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Search failed')
      console.error('Search error:', err)
    } finally {
      setIsSearching(false)
    }
  }

  return (
    <div className="h-full flex flex-col p-6 gap-6">
      {/* 标题 */}
      <div className="border-b pb-4">
        <h1 className="text-3xl font-bold text-gray-900">知识库管理</h1>
        <p className="text-gray-600 mt-1">上传、管理和搜索文档，支持 RAG 工作流集成</p>
      </div>

      {/* 错误提示 */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
          <p className="font-medium">错误：{error}</p>
        </div>
      )}

      {/* 主要布局：三列 */}
      <div className="flex-1 grid grid-cols-4 gap-4">
        {/* 左列：文档列表 */}
        <div className="col-span-1 flex flex-col gap-4">
          <div className="border rounded-lg overflow-hidden bg-white flex-1 flex flex-col">
            <div className="bg-gray-50 border-b px-4 py-3 font-semibold text-sm">
              我的文档 ({documents.length})
            </div>
            <div className="flex-1 overflow-auto">
              <DocumentsList
                documents={documents}
                selectedDocId={selectedDocId}
                onSelectDoc={setSelectedDocId}
                isLoading={isLoadingDocs}
              />
            </div>
          </div>
        </div>

        {/* 中列：上传和搜索 */}
        <div className="col-span-2 flex flex-col gap-4">
          {/* 上传区域 */}
          <UploadSection onDocumentUploaded={handleDocumentUploaded} />

          {/* 搜索区域 */}
          <SearchSection
            onSearch={handleSearch}
            isLoading={isSearching}
            disabled={documents.length === 0}
          />

          {/* 搜索结果 */}
          {searchResults && (
            <div className="flex-1 overflow-auto">
              <SearchResults results={searchResults} />
            </div>
          )}
        </div>

        {/* 右列：文档详情 */}
        <div className="col-span-1">
          {selectedDocId && (
            <DocumentDetail
              documentId={selectedDocId}
              onDeleted={handleDocumentDeleted}
            />
          )}
          {!selectedDocId && (
            <Card className="h-full flex items-center justify-center text-center p-6">
              <div className="text-gray-500">
                <p className="text-sm">选择一个文档查看详情</p>
              </div>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}
