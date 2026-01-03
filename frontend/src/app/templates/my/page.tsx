'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { Plus, Star, Download, Eye, Trash2, Edit } from 'lucide-react'
import axios from 'axios'
import { useAuthStore } from '@/stores/auth-store'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface MyTemplate {
  id: string
  name: string
  description: string
  category: string
  icon_url?: string
  rating: number
  use_count: number
  favorite_count: number
  is_featured: boolean
  created_at: string
  updated_at: string
}

export default function MyTemplatesPage() {
  const router = useRouter()
  const { isAuthenticated } = useAuthStore()
  const [templates, setTemplates] = useState<MyTemplate[]>([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/auth/login')
      return
    }
    loadTemplates()
  }, [isAuthenticated, router])

  const loadTemplates = async () => {
    try {
      setIsLoading(true)
      const token = localStorage.getItem('accessToken')
      if (!token) throw new Error('No access token found')

      // This would call an endpoint to get user's published templates
      // For now, we'll fetch from marketplace and filter
      // In a real app, you'd have a dedicated endpoint
      setTemplates([])
    } catch (error) {
      console.error('Failed to load templates:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleDelete = async (templateId: string) => {
    if (!confirm('Are you sure you want to delete this template?')) return

    try {
      const token = localStorage.getItem('accessToken')
      if (!token) throw new Error('No access token found')

      await axios.delete(
        `${API_URL}/api/v1/marketplace/templates/${templateId}`,
        { headers: { Authorization: `Bearer ${token}` } }
      )

      setTemplates(templates.filter(t => t.id !== templateId))
    } catch (error) {
      console.error('Failed to delete template:', error)
      alert('Failed to delete template')
    }
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto px-6 py-8 max-w-6xl">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold">My Templates</h1>
            <p className="text-muted-foreground mt-1">Manage your published templates</p>
          </div>
          <Link
            href="/workflows"
            className="flex items-center gap-2 px-6 py-3 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90"
          >
            <Plus className="w-5 h-5" />
            Publish New
          </Link>
        </div>

        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <div className="text-lg">Loading templates...</div>
          </div>
        ) : templates.length === 0 ? (
          <div className="text-center py-12 border border-dashed border-border rounded-xl">
            <p className="text-muted-foreground mb-4">No templates published yet</p>
            <p className="text-sm text-muted-foreground mb-6">
              Create a workflow and publish it to the marketplace
            </p>
            <Link
              href="/workspace"
              className="inline-flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90"
            >
              Create Workflow
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {templates.map((template) => (
              <div
                key={template.id}
                className="border border-border rounded-xl overflow-hidden hover:border-primary transition-all hover:shadow-lg"
              >
                {/* Image */}
                <div className="aspect-video bg-gradient-to-br from-purple-500/20 to-pink-500/20 flex items-center justify-center">
                  {template.icon_url ? (
                    <img
                      src={template.icon_url}
                      alt={template.name}
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <Download className="w-8 h-8 text-muted-foreground" />
                  )}
                </div>

                {/* Content */}
                <div className="p-4">
                  <div className="flex items-start justify-between mb-2">
                    <h3 className="font-semibold line-clamp-2">{template.name}</h3>
                    {template.is_featured && (
                      <span className="px-2 py-1 bg-yellow-500/20 text-yellow-600 rounded text-xs flex-shrink-0">
                        Featured
                      </span>
                    )}
                  </div>

                  <p className="text-sm text-muted-foreground mb-3 line-clamp-2">
                    {template.description}
                  </p>

                  <div className="flex items-center gap-3 text-xs text-muted-foreground mb-4">
                    <div className="flex items-center gap-1">
                      <Star className="w-4 h-4" />
                      <span>{template.rating.toFixed(1)}</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <Download className="w-4 h-4" />
                      <span>{template.use_count}</span>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex gap-2">
                    <button className="flex-1 flex items-center justify-center gap-2 px-3 py-2 border border-border rounded-lg hover:bg-accent text-sm">
                      <Edit className="w-4 h-4" />
                      Edit
                    </button>
                    <button
                      onClick={() => handleDelete(template.id)}
                      className="flex-1 flex items-center justify-center gap-2 px-3 py-2 border border-destructive/30 text-destructive rounded-lg hover:bg-destructive/10 text-sm"
                    >
                      <Trash2 className="w-4 h-4" />
                      Delete
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
