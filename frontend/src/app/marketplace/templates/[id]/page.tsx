'use client'

import { useEffect, useState } from 'react'
import { useRouter, useParams } from 'next/navigation'
import Link from 'next/link'
import { Star, Heart, Download, Share2, MessageCircle, ArrowLeft, Sparkles, AlertCircle } from 'lucide-react'
import axios from 'axios'
import { useAuthStore } from '@/stores/auth-store'
import { useMarketplaceStore } from '@/stores/marketplace-store'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface TemplateDetail {
  id: string
  name: string
  description: string
  category: string
  tags?: string[]
  icon_url?: string
  author_id: string
  use_count: number
  favorite_count: number
  rating: number
  review_count: number
  is_featured: boolean
  is_published: boolean
  created_at: string
  updated_at: string
}

interface Review {
  id: string
  rating: number
  comment?: string
  created_at: string
}

export default function TemplateDetailPage() {
  const router = useRouter()
  const params = useParams()
  const { isAuthenticated } = useAuthStore()
  const { isFavorited, toggleFavorite, favoriteLoadingIds, fetchUserFavorites } = useMarketplaceStore()
  
  const [template, setTemplate] = useState<TemplateDetail | null>(null)
  const [reviews, setReviews] = useState<Review[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isUsing, setIsUsing] = useState(false)

  const templateId = params.id as string

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/auth/login')
      return
    }
    loadTemplate()
    fetchUserFavorites() // Load user's favorites
  }, [isAuthenticated, router, templateId, fetchUserFavorites])

  const loadTemplate = async () => {
    try {
      setIsLoading(true)
      const token = localStorage.getItem('accessToken')
      if (!token) throw new Error('No access token found')

      const response = await axios.get(
        `${API_URL}/api/v1/marketplace/templates/${templateId}`,
        { headers: { Authorization: `Bearer ${token}` } }
      )
      setTemplate(response.data)

      // Load reviews
      try {
        const reviewsResponse = await axios.get(
          `${API_URL}/api/v1/marketplace/templates/${templateId}/reviews`,
          { headers: { Authorization: `Bearer ${token}` } }
        )
        setReviews(reviewsResponse.data)
      } catch (err) {
        console.error('Failed to load reviews:', err)
      }
    } catch (err: any) {
      console.error('Failed to load template:', err)
      setError(err.response?.data?.detail || 'Failed to load template')
    } finally {
      setIsLoading(false)
    }
  }

  const handleUseTemplate = async () => {
    try {
      setIsUsing(true)
      const token = localStorage.getItem('accessToken')
      if (!token) throw new Error('No access token found')

      const response = await axios.post(
        `${API_URL}/api/v1/marketplace/templates/${templateId}/use`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      )

      // Redirect to editor with the new workflow
      router.push(`/workflows/${response.data.id}`)
    } catch (err: any) {
      console.error('Failed to create workflow from template:', err)
      alert(err.response?.data?.detail || 'Failed to create workflow')
    } finally {
      setIsUsing(false)
    }
  }

  const handleFavorite = async () => {
    try {
      await toggleFavorite(templateId)
    } catch (err: any) {
      console.error('Failed to toggle favorite:', err)
      alert(err.response?.data?.detail || 'Failed to update favorite')
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-lg">Loading template...</div>
      </div>
    )
  }

  if (error || !template) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen gap-4">
        <AlertCircle className="w-12 h-12 text-destructive" />
        <div className="text-lg">{error || 'Template not found'}</div>
        <Link
          href="/marketplace"
          className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90"
        >
          Back to Marketplace
        </Link>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto px-6 py-8 max-w-4xl">
        {/* Navigation */}
        <div className="flex items-center gap-3 mb-8">
          <button
            onClick={() => router.back()}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition-colors font-medium"
          >
            <ArrowLeft className="w-4 h-4" />
            Back
          </button>
          <span className="text-slate-600">/</span>
          <Link
            href="/marketplace"
            className="text-slate-400 hover:text-white transition-colors"
          >
            Marketplace
          </Link>
          <span className="text-slate-600">/</span>
          <span className="text-slate-400">Template</span>
        </div>

        {/* Content */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* Main Content */}
          <div className="md:col-span-2">
            {/* Image */}
            <div className="aspect-video bg-gradient-to-br from-purple-500/20 to-pink-500/20 rounded-xl flex items-center justify-center mb-6 overflow-hidden">
              {template.icon_url ? (
                <img
                  src={template.icon_url}
                  alt={template.name}
                  className="w-full h-full object-cover"
                />
              ) : (
                <Sparkles className="w-24 h-24 text-muted-foreground" />
              )}
            </div>

            {/* Title and Info */}
            <h1 className="text-4xl font-bold mb-2">{template.name}</h1>
            <div className="flex items-center gap-4 mb-6 text-muted-foreground">
              <div className="flex items-center gap-1">
                <Star className="w-4 h-4" />
                <span>{template.rating.toFixed(1)} ({template.review_count} reviews)</span>
              </div>
              <div className="flex items-center gap-1">
                <Download className="w-4 h-4" />
                <span>{template.use_count} uses</span>
              </div>
              {template.is_featured && (
                <span className="px-2 py-1 bg-yellow-500/20 text-yellow-600 rounded text-sm">
                  Featured
                </span>
              )}
            </div>

            {/* Description */}
            <div className="prose prose-invert max-w-none mb-6">
              <p className="text-lg text-muted-foreground">{template.description}</p>
            </div>

            {/* Tags */}
            {template.tags && template.tags.length > 0 && (
              <div className="flex flex-wrap gap-2 mb-6">
                {template.tags.map((tag) => (
                  <span
                    key={tag}
                    className="px-3 py-1 bg-accent rounded-full text-sm"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            )}

            {/* Reviews Section */}
            <div className="border-t border-border pt-6">
              <h2 className="text-2xl font-bold mb-4">Reviews</h2>
              {reviews.length === 0 ? (
                <p className="text-muted-foreground">No reviews yet</p>
              ) : (
                <div className="space-y-4">
                  {reviews.map((review) => (
                    <div
                      key={review.id}
                      className="border border-border rounded-lg p-4"
                    >
                      <div className="flex items-center gap-2 mb-2">
                        <div className="flex items-center gap-1">
                          {[...Array(5)].map((_, i) => (
                            <Star
                              key={i}
                              className={`w-4 h-4 ${
                                i < review.rating
                                  ? 'fill-yellow-500 text-yellow-500'
                                  : 'text-muted-foreground'
                              }`}
                            />
                          ))}
                        </div>
                        <span className="text-sm text-muted-foreground">
                          {new Date(review.created_at).toLocaleDateString()}
                        </span>
                      </div>
                      {review.comment && (
                        <p className="text-sm text-muted-foreground">{review.comment}</p>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Sidebar */}
          <div className="md:col-span-1">
            {/* Action Card */}
            <div className="bg-accent/50 rounded-xl p-6 mb-6 sticky top-6">
              <button
                onClick={handleUseTemplate}
                disabled={isUsing}
                className="w-full px-6 py-3 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 font-medium mb-3 disabled:opacity-50"
              >
                {isUsing ? 'Creating...' : 'Use Template'}
              </button>

              <button
                onClick={handleFavorite}
                disabled={favoriteLoadingIds.has(templateId)}
                className={`w-full flex items-center justify-center gap-2 px-6 py-3 border border-border rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${
                  isFavorited(templateId)
                    ? 'bg-red-500/10 border-red-500/30 text-red-600'
                    : 'hover:bg-accent'
                }`}
              >
                <Heart
                  className={`w-5 h-5 ${isFavorited(templateId) ? 'fill-current' : ''}`}
                />
                {isFavorited(templateId) ? 'Favorited' : 'Add to Favorites'}
              </button>

              <button className="w-full flex items-center justify-center gap-2 px-6 py-3 border border-border rounded-lg hover:bg-accent mt-3">
                <Share2 className="w-5 h-5" />
                Share
              </button>
            </div>

            {/* Info Card */}
            <div className="bg-accent/50 rounded-xl p-6">
              <h3 className="font-semibold mb-4">Information</h3>
              <div className="space-y-3 text-sm">
                <div>
                  <p className="text-muted-foreground mb-1">Category</p>
                  <p className="font-medium">{template.category}</p>
                </div>
                <div>
                  <p className="text-muted-foreground mb-1">Created</p>
                  <p className="font-medium">
                    {new Date(template.created_at).toLocaleDateString()}
                  </p>
                </div>
                <div>
                  <p className="text-muted-foreground mb-1">Rating</p>
                  <div className="flex items-center gap-2">
                    <div className="flex items-center gap-1">
                      {[...Array(5)].map((_, i) => (
                        <Star
                          key={i}
                          className={`w-4 h-4 ${
                            i < Math.round(template.rating)
                              ? 'fill-yellow-500 text-yellow-500'
                              : 'text-muted-foreground'
                          }`}
                        />
                      ))}
                    </div>
                    <span>{template.rating.toFixed(1)}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
