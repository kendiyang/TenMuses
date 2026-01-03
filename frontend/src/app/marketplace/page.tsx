'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import axios from 'axios'
import { Search, Star, Heart, TrendingUp, ArrowLeft } from 'lucide-react'
import { useAuthStore } from '@/stores/auth-store'
import { useMarketplaceStore } from '@/stores/marketplace-store'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function MarketplacePage() {
  const router = useRouter()
  const { isAuthenticated } = useAuthStore()
  const {
    templates,
    categories,
    isLoadingTemplates,
    searchQuery,
    selectedCategory,
    fetchTemplates,
    fetchFeaturedTemplates,
    fetchUserFavorites,
    toggleFavorite,
    isFavorited,
    favoriteLoadingIds,
    setSearchQuery,
    setSelectedCategory,
  } = useMarketplaceStore()
  const [selectedCategoryLocal, setSelectedCategoryLocal] = useState<string | null>(null)

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/auth/login')
      return
    }
    fetchTemplates()
    fetchFeaturedTemplates()
    fetchUserFavorites()
  }, [isAuthenticated, router, fetchTemplates, fetchFeaturedTemplates, fetchUserFavorites])

  const handleUseTemplate = async (templateId: string) => {
    try {
      const token = localStorage.getItem('accessToken')
      if (!token) throw new Error('No access token found')

      const response = await axios.post(
        `${API_URL}/api/v1/marketplace/templates/${templateId}/use`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      )
      
      router.push(`/workflows/${response.data.id}`)
    } catch (error: any) {
      console.error('Failed to use template:', error)
      alert(error.response?.data?.detail || 'Failed to use template')
    }
  }

  const filteredTemplates = selectedCategoryLocal
    ? templates.filter((t) => t.category === selectedCategoryLocal)
    : templates

  const topPicksTemplates = templates.slice(0, 3)

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto px-6 py-12 max-w-7xl">
        {/* Navigation Header */}
        <div className="mb-8 flex items-center gap-4">
          <button
            onClick={() => router.push('/workspace')}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition-colors font-medium"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Workspace
          </button>
        </div>

        {/* Header */}
        <div className="mb-12">
          <h1 className="text-4xl font-bold mb-2">Template Marketplace</h1>
          <p className="text-muted-foreground">Discover and use pre-built AI workflows</p>
        </div>

        {/* Top Picks Section */}
        <div className="mb-16">
          <h2 className="text-2xl font-bold mb-6">Top Picks</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {topPicksTemplates.map((template) => (
              <div
                key={template.id}
                onClick={() => router.push(`/marketplace/templates/${template.id}`)}
                className="group relative overflow-hidden rounded-2xl bg-gradient-to-br from-slate-900 to-slate-800 p-6 hover:shadow-2xl transition-all duration-300 cursor-pointer min-h-64 flex flex-col justify-between"
              >
                <div>
                  <div className="inline-block bg-primary/20 text-primary px-3 py-1 rounded-full text-xs font-semibold mb-4">
                    {template.category}
                  </div>
                  <h3 className="text-xl font-bold text-white mb-2">{template.name}</h3>
                  <p className="text-sm text-slate-300 line-clamp-2">{template.description}</p>
                </div>
                <button 
                  onClick={(e) => {
                    e.stopPropagation()
                    handleUseTemplate(template.id)
                  }}
                  className="bg-primary hover:bg-primary/90 text-white px-4 py-2 rounded-lg text-sm font-semibold w-fit transition-colors"
                >
                  Try it now
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* All Templates Section */}
        <div>
          <div className="flex items-center justify-between mb-8">
            <h2 className="text-2xl font-bold">All Templates</h2>
            <div className="relative w-64">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <input
                type="text"
                placeholder="Search templates..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>
          </div>

          {/* Category Filter */}
          <div className="flex gap-3 mb-8 overflow-x-auto pb-2">
            <button
              onClick={() => setSelectedCategoryLocal(null)}
              className={`px-4 py-2 rounded-full font-semibold whitespace-nowrap transition-colors ${
                selectedCategoryLocal === null
                  ? 'bg-primary text-white'
                  : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
              }`}
            >
              Featured
            </button>
            {categories.map((cat) => (
              <button
                key={cat}
                onClick={() => setSelectedCategoryLocal(cat)}
                className={`px-4 py-2 rounded-full font-semibold whitespace-nowrap transition-colors ${
                  selectedCategoryLocal === cat
                    ? 'bg-primary text-white'
                    : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                }`}
              >
                {cat}
              </button>
            ))}
          </div>

          {/* Templates Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {isLoadingTemplates ? (
              <div className="col-span-full flex items-center justify-center py-12">
                <div className="text-center">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
                  <p className="text-muted-foreground">Loading templates...</p>
                </div>
              </div>
            ) : filteredTemplates.length === 0 ? (
              <div className="col-span-full flex items-center justify-center py-12">
                <p className="text-muted-foreground">No templates found</p>
              </div>
            ) : (
              filteredTemplates.map((template) => (
                <div
                  key={template.id}
                  onClick={() => router.push(`/marketplace/templates/${template.id}`)}
                  className="group rounded-xl border border-border overflow-hidden hover:shadow-lg hover:border-primary/50 transition-all duration-300 cursor-pointer bg-slate-900/50"
                >
                  {/* Template Image Placeholder */}
                  <div className="h-48 bg-gradient-to-br from-slate-800 to-slate-900 flex items-center justify-center group-hover:from-slate-700 group-hover:to-slate-800 transition-colors">
                    <div className="text-center">
                      <TrendingUp className="w-8 h-8 text-primary mx-auto mb-2" />
                      <p className="text-xs text-slate-400">{template.category}</p>
                    </div>
                  </div>

                  {/* Template Info */}
                  <div className="p-4">
                    <h3 className="font-bold text-lg mb-2 line-clamp-2">{template.name}</h3>
                    <p className="text-sm text-slate-400 mb-4 line-clamp-2">{template.description}</p>

                    {/* Author & Stats */}
                    <div className="flex items-center justify-between text-xs text-slate-500 mb-4">
                      <span className="flex items-center gap-1">
                        <div className="w-5 h-5 rounded-full bg-primary/20 flex items-center justify-center text-primary text-xs">
                          {template.author_id.charAt(0).toUpperCase()}
                        </div>
                        {template.author_id}
                      </span>
                    </div>

                    {/* Stats Footer */}
                    <div className="flex items-center justify-between pt-4 border-t border-border/50">
                      <div className="flex items-center gap-4">
                        <span className="flex items-center gap-1 text-slate-400 text-xs">
                          <Star className="w-4 h-4 text-yellow-500 fill-yellow-500" />
                          {template.rating.toFixed(1)}
                        </span>
                        <span className="flex items-center gap-1 text-slate-400 text-xs">
                          <TrendingUp className="w-4 h-4 text-blue-500" />
                          {template.use_count} runs
                        </span>
                      </div>
                      <button 
                        onClick={(e) => {
                          e.stopPropagation()
                          toggleFavorite(template.id)
                        }}
                        disabled={favoriteLoadingIds.has(template.id)}
                        className="p-2 hover:bg-primary/10 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        <Heart 
                          className={`w-4 h-4 transition-colors ${
                            isFavorited(template.id) 
                              ? 'text-primary fill-primary' 
                              : 'text-slate-400 hover:text-primary'
                          }`}
                        />
                      </button>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
