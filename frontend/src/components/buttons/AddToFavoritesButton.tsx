'use client'

import { useState } from 'react'
import { Heart } from 'lucide-react'
import { useFavoritesStore } from '@/stores/favorites-store'

interface AddToFavoritesButtonProps {
  templateId: string
  className?: string
  showLabel?: boolean
  onSuccess?: () => void
}

export default function AddToFavoritesButton({
  templateId,
  className = '',
  showLabel = true,
  onSuccess,
}: AddToFavoritesButtonProps) {
  const { isFavorited, addFavorite, removeFavorite, error } = useFavoritesStore()
  const [loading, setLoading] = useState(false)
  const isFav = isFavorited(templateId)

  const handleToggleFavorite = async (e: React.MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()

    setLoading(true)
    try {
      if (isFav) {
        await removeFavorite(templateId)
      } else {
        await addFavorite(templateId)
      }
      onSuccess?.()
    } catch (err) {
      console.error('Failed to update favorite:', err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <button
      onClick={handleToggleFavorite}
      disabled={loading}
      className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors disabled:opacity-50 ${
        isFav
          ? 'bg-red-50 text-red-600 hover:bg-red-100 border border-red-200'
          : 'border border-border hover:bg-muted'
      } ${className}`}
      title={isFav ? 'Remove from favorites' : 'Add to favorites'}
    >
      <Heart className={`w-4 h-4 ${isFav ? 'fill-current' : ''}`} />
      {showLabel && (isFav ? 'Favorited' : 'Add to Favorites')}
    </button>
  )
}
