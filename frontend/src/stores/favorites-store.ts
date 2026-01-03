import { create } from 'zustand'
import { apiClient } from '@/lib/api-client'

interface Template {
  id: string
  name: string
  description: string
  category: string
  tags?: string[]
  icon_url?: string
  rating?: number
  use_count?: number
  is_featured?: boolean
}

interface FavoritesState {
  favorites: Template[]
  loading: boolean
  error: string | null
  isFavorited: (templateId: string) => boolean
  addFavorite: (templateId: string) => Promise<void>
  removeFavorite: (templateId: string) => Promise<void>
  fetchFavorites: () => Promise<void>
  clearError: () => void
}

export const useFavoritesStore = create<FavoritesState>((set, get) => ({
  favorites: [],
  loading: false,
  error: null,

  isFavorited: (templateId: string) => {
    const state = get()
    return state.favorites.some((fav) => fav.id === templateId)
  },

  addFavorite: async (templateId: string) => {
    try {
      set({ error: null })
      await apiClient.post(`/marketplace/templates/${templateId}/favorite`)

      // Fetch updated favorites list
      await get().fetchFavorites()
    } catch (err: any) {
      const errorMessage = err?.response?.data?.detail || 'Failed to add favorite'
      set({ error: errorMessage })
      throw err
    }
  },

  removeFavorite: async (templateId: string) => {
    try {
      set({ error: null })
      await apiClient.delete(`/marketplace/templates/${templateId}/favorite`)

      // Remove from local state immediately
      set((state) => ({
        favorites: state.favorites.filter((fav) => fav.id !== templateId),
      }))
    } catch (err: any) {
      const errorMessage = err?.response?.data?.detail || 'Failed to remove favorite'
      set({ error: errorMessage })
      throw err
    }
  },

  fetchFavorites: async () => {
    set({ loading: true, error: null })
    try {
      const data = await apiClient.get<Template[]>('/marketplace/favorites')
      set({ favorites: data, loading: false })
    } catch (err: any) {
      const errorMessage = err?.response?.data?.detail || 'Failed to fetch favorites'
      set({ error: errorMessage, loading: false })
    }
  },

  clearError: () => set({ error: null }),
}))
