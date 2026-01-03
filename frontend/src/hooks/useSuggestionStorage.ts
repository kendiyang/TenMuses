'use client'

import { useState, useCallback, useEffect } from 'react'
import { SuggestionStorage, type StoredSuggestion, type SuggestionFilter } from '@/lib/suggestion-storage'

/**
 * React hook for interacting with suggestion storage
 * 
 * Provides reactive state management and methods for:
 * - Saving suggestions
 * - Loading/filtering suggestions
 * - Managing favorites
 * - Export/import
 * - Statistics
 * 
 * Example:
 * ```tsx
 * const { suggestions, save, toggleFavorite, stats } = useSuggestionStorage()
 * 
 * // Save a new suggestion
 * save({
 *   id: 'unique-id',
 *   type: 'workflow',
 *   content: 'RAG workflow with vector search',
 *   timestamp: Date.now()
 * })
 * 
 * // Toggle favorite
 * toggleFavorite('suggestion-id')
 * ```
 */
export function useSuggestionStorage() {
  const [suggestions, setSuggestions] = useState<StoredSuggestion[]>([])
  const [stats, setStats] = useState({
    total: 0,
    favorites: 0,
    workflows: 0,
    nodes: 0
  })

  // Load initial data
  useEffect(() => {
    refresh()
  }, [])

  /**
   * Refresh suggestions from storage and update state
   */
  const refresh = useCallback(() => {
    const all = SuggestionStorage.getAll()
    setSuggestions(all)
    setStats(SuggestionStorage.getStats())
  }, [])

  /**
   * Save a suggestion to storage
   */
  const save = useCallback((suggestion: StoredSuggestion) => {
    SuggestionStorage.saveSuggestion(suggestion)
    refresh()
  }, [refresh])

  /**
   * Get all suggestions
   */
  const getAll = useCallback((): StoredSuggestion[] => {
    return SuggestionStorage.getAll()
  }, [])

  /**
   * Get favorite suggestions
   */
  const getFavorites = useCallback((): StoredSuggestion[] => {
    return SuggestionStorage.getFavorites()
  }, [])

  /**
   * Toggle favorite status of a suggestion
   */
  const toggleFavorite = useCallback((id: string): boolean => {
    const result = SuggestionStorage.toggleFavorite(id)
    if (result) {
      refresh()
    }
    return result
  }, [refresh])

  /**
   * Search/filter suggestions
   */
  const search = useCallback((filter: SuggestionFilter): StoredSuggestion[] => {
    return SuggestionStorage.search(filter)
  }, [])

  /**
   * Remove a suggestion
   */
  const remove = useCallback((id: string): boolean => {
    const result = SuggestionStorage.removeSuggestion(id)
    if (result) {
      refresh()
    }
    return result
  }, [refresh])

  /**
   * Clear all suggestions
   */
  const clear = useCallback(() => {
    SuggestionStorage.clear()
    refresh()
  }, [refresh])

  /**
   * Clear old suggestions (older than N days)
   */
  const clearOld = useCallback((daysOld: number = 30): number => {
    const removed = SuggestionStorage.clearOld(daysOld)
    refresh()
    return removed
  }, [refresh])

  /**
   * Get storage statistics
   */
  const getStats = useCallback(() => {
    return SuggestionStorage.getStats()
  }, [])

  /**
   * Export suggestions as JSON string
   */
  const exportData = useCallback((): string => {
    return SuggestionStorage.export()
  }, [])

  /**
   * Import suggestions from JSON string
   */
  const importData = useCallback((jsonData: string): boolean => {
    const result = SuggestionStorage.import(jsonData)
    if (result) {
      refresh()
    }
    return result
  }, [refresh])

  return {
    // State
    suggestions,
    stats,

    // Methods
    save,
    getAll,
    getFavorites,
    toggleFavorite,
    search,
    remove,
    clear,
    clearOld,
    getStats,
    export: exportData,
    import: importData,
    refresh
  }
}
