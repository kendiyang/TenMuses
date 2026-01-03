/**
 * Upload Section Component
 * 路径: frontend/src/components/knowledge/UploadSection.tsx
 */

'use client'

import React, { useRef, useState } from 'react'
import { Card } from '@/components/ui/card'
import { Upload, X, CheckCircle2 } from 'lucide-react'

interface UploadSectionProps {
  onDocumentUploaded?: (doc: any) => void
}

export default function UploadSection({ onDocumentUploaded }: UploadSectionProps) {
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [isDragActive, setIsDragActive] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [uploadedFile, setUploadedFile] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const SUPPORTED_FORMATS = ['PDF', 'DOCX', 'TXT', 'MD']
  const SUPPORTED_MIMES = [
    'application/pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'text/plain',
    'text/markdown',
  ]

  const validateFile = (file: File): string | null => {
    // 检查文件大小（100MB）
    if (file.size > 100 * 1024 * 1024) {
      return '文件大小不能超过 100MB'
    }

    // 检查文件格式
    if (!SUPPORTED_MIMES.includes(file.type)) {
      const ext = file.name.split('.').pop()?.toUpperCase()
      if (!SUPPORTED_FORMATS.includes(ext || '')) {
        return `不支持的文件格式: ${ext}。支持: ${SUPPORTED_FORMATS.join(', ')}`
      }
    }

    return null
  }

  const uploadFile = async (file: File) => {
    try {
      const validationError = validateFile(file)
      if (validationError) {
        setError(validationError)
        return
      }

      setIsUploading(true)
      setError(null)
      setUploadedFile(null)
      setUploadProgress(0)

      const formData = new FormData()
      formData.append('file', file)
      formData.append('metadata', JSON.stringify({ source: 'web-upload' }))

      // 模拟上传进度（实际使用 XMLHttpRequest 或 fetch with ReadableStream）
      const progressInterval = setInterval(() => {
        setUploadProgress((prev) => {
          if (prev >= 90) return 90
          return prev + Math.random() * 30
        })
      }, 200)

      const response = await fetch('/api/v1/kb/upload', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${localStorage.getItem('accessToken')}`,
        },
        body: formData,
      })

      clearInterval(progressInterval)
      setUploadProgress(100)

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.message || 'Upload failed')
      }

      const data = await response.json()
      setUploadedFile(file.name)
      onDocumentUploaded?.(data)

      // 3 秒后清除成功提示
      setTimeout(() => {
        setUploadedFile(null)
        setUploadProgress(0)
      }, 3000)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed')
      console.error('Upload error:', err)
    } finally {
      setIsUploading(false)
    }
  }

  const handleDragEnter = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragActive(true)
  }

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragActive(false)
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragActive(false)

    const files = e.dataTransfer.files
    if (files.length > 0) {
      uploadFile(files[0])
    }
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.currentTarget.files
    if (files && files.length > 0) {
      uploadFile(files[0])
    }
  }

  return (
    <Card className="p-6 bg-gradient-to-br from-blue-50 to-indigo-50 border-2 border-dashed border-blue-200">
      <div
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDragOver={handleDragOver}
        onDrop={handleDrop}
        className={`text-center py-8 cursor-pointer transition-colors ${
          isDragActive ? 'bg-blue-100 rounded-lg' : ''
        }`}
        onClick={() => fileInputRef.current?.click()}
      >
        {uploadedFile ? (
          <div className="space-y-2">
            <CheckCircle2 className="h-12 w-12 text-green-600 mx-auto" />
            <p className="text-green-700 font-medium">上传成功！</p>
            <p className="text-sm text-green-600">{uploadedFile}</p>
          </div>
        ) : isUploading ? (
          <div className="space-y-4">
            <p className="text-gray-700 font-medium">上传中...</p>
            <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
              <div
                className="bg-blue-600 h-full transition-all duration-300"
                style={{ width: `${uploadProgress}%` }}
              />
            </div>
            <p className="text-sm text-gray-600">{Math.round(uploadProgress)}%</p>
          </div>
        ) : error ? (
          <div className="space-y-3">
            <X className="h-12 w-12 text-red-600 mx-auto" />
            <p className="text-red-700 font-medium">上传失败</p>
            <p className="text-sm text-red-600">{error}</p>
            <button
              onClick={() => {
                setError(null)
                fileInputRef.current?.click()
              }}
              className="mt-2 px-4 py-1 bg-red-100 text-red-700 rounded hover:bg-red-200 text-sm"
            >
              重新上传
            </button>
          </div>
        ) : (
          <div className="space-y-3">
            <Upload className="h-12 w-12 text-blue-600 mx-auto" />
            <div>
              <p className="font-medium text-gray-900">拖拽文件或点击上传</p>
              <p className="text-sm text-gray-600 mt-1">
                支持: {SUPPORTED_FORMATS.join(', ')} (最大 100MB)
              </p>
            </div>
          </div>
        )}
      </div>

      <input
        ref={fileInputRef}
        type="file"
        accept={SUPPORTED_MIMES.join(',')}
        onChange={handleFileSelect}
        className="hidden"
        disabled={isUploading}
      />
    </Card>
  )
}
