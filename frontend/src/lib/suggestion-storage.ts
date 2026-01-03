/**
 * Suggestion Storage Library
 * 
 * 管理建议的本地存储和检索
 */

export interface StoredSuggestion {
  id: string
  timestamp: number
  type: 'workflow' | 'node'
  content: {
    name?: string
    label?: string
    description?: string
    [key: string]: any
  }
  isFavorite: boolean
  context?: {
    workflowId?: string
    nodeCount?: number
    complexity?: string
  }
  tags?: string[]
}

export interface SuggestionFilter {
  type?: 'workflow' | 'node'
  favorite?: boolean
  tags?: string[]
  searchText?: string
  dateRange?: {
    start: number
    end: number
  }
}

export class SuggestionStorage {
  private static readonly STORAGE_KEY = 'copilot_suggestions'
  private static readonly MAX_ITEMS = 100
  private static readonly VERSION = 1

  /**
   * 保存建议到本地存储
   */
  static saveSuggestion(suggestion: StoredSuggestion): void {
    try {
      const all = this.getAll()
      
      // 检查重复 (基于内容的哈希)
      const hash = this.generateHash(suggestion)
      const existing = all.findIndex(s => this.generateHash(s) === hash)
      
      if (existing >= 0) {
        // 更新现有建议
        all[existing].timestamp = Date.now()
        all[existing].isFavorite = suggestion.isFavorite || all[existing].isFavorite
      } else {
        // 添加新建议到顶部
        all.unshift(suggestion)
      }
      
      // 保持最多 100 条
      if (all.length > this.MAX_ITEMS) {
        all.splice(this.MAX_ITEMS)
      }
      
      this.persist(all)
    } catch (error) {
      console.error('Failed to save suggestion:', error)
    }
  }

  /**
   * 获取所有建议
   */
  static getAll(): StoredSuggestion[] {
    try {
      const stored = localStorage.getItem(this.STORAGE_KEY)
      if (!stored) return []
      
      const parsed = JSON.parse(stored)
      return Array.isArray(parsed) ? parsed : []
    } catch (error) {
      console.error('Failed to load suggestions:', error)
      return []
    }
  }

  /**
   * 获取收藏的建议
   */
  static getFavorites(): StoredSuggestion[] {
    return this.getAll().filter(s => s.isFavorite)
  }

  /**
   * 切换建议的收藏状态
   */
  static toggleFavorite(id: string): boolean {
    try {
      const all = this.getAll()
      const item = all.find(s => s.id === id)
      
      if (!item) return false
      
      item.isFavorite = !item.isFavorite
      item.timestamp = Date.now() // 更新时间戳
      this.persist(all)
      
      return item.isFavorite
    } catch (error) {
      console.error('Failed to toggle favorite:', error)
      return false
    }
  }

  /**
   * 设置建议标签
   */
  static addTags(id: string, tags: string[]): void {
    try {
      const all = this.getAll()
      const item = all.find(s => s.id === id)
      
      if (!item) return
      
      item.tags = [...new Set([...(item.tags || []), ...tags])]
      this.persist(all)
    } catch (error) {
      console.error('Failed to add tags:', error)
    }
  }

  /**
   * 删除建议标签
   */
  static removeTags(id: string, tags: string[]): void {
    try {
      const all = this.getAll()
      const item = all.find(s => s.id === id)
      
      if (!item || !item.tags) return
      
      item.tags = item.tags.filter(t => !tags.includes(t))
      this.persist(all)
    } catch (error) {
      console.error('Failed to remove tags:', error)
    }
  }

  /**
   * 搜索建议
   */
  static search(filter: SuggestionFilter): StoredSuggestion[] {
    let results = this.getAll()

    // 按类型过滤
    if (filter.type) {
      results = results.filter(s => s.type === filter.type)
    }

    // 按收藏过滤
    if (filter.favorite !== undefined) {
      results = results.filter(s => s.isFavorite === filter.favorite)
    }

    // 按标签过滤
    if (filter.tags && filter.tags.length > 0) {
      results = results.filter(s => {
        const sTags = s.tags || []
        return filter.tags!.some(t => sTags.includes(t))
      })
    }

    // 按文本搜索
    if (filter.searchText) {
      const searchLower = filter.searchText.toLowerCase()
      results = results.filter(s => {
        const text = JSON.stringify(s.content).toLowerCase()
        return text.includes(searchLower)
      })
    }

    // 按日期范围过滤
    if (filter.dateRange) {
      results = results.filter(
        s => s.timestamp >= filter.dateRange!.start && 
             s.timestamp <= filter.dateRange!.end
      )
    }

    return results
  }

  /**
   * 删除建议
   */
  static removeSuggestion(id: string): boolean {
    try {
      const all = this.getAll()
      const index = all.findIndex(s => s.id === id)
      
      if (index < 0) return false
      
      all.splice(index, 1)
      this.persist(all)
      
      return true
    } catch (error) {
      console.error('Failed to remove suggestion:', error)
      return false
    }
  }

  /**
   * 清空所有建议
   */
  static clear(): void {
    try {
      localStorage.removeItem(this.STORAGE_KEY)
    } catch (error) {
      console.error('Failed to clear storage:', error)
    }
  }

  /**
   * 清空旧建议 (超过 30 天)
   */
  static clearOld(daysOld: number = 30): number {
    try {
      const all = this.getAll()
      const cutoffTime = Date.now() - daysOld * 24 * 60 * 60 * 1000
      
      const toKeep = all.filter(s => s.timestamp > cutoffTime || s.isFavorite)
      const removed = all.length - toKeep.length
      
      this.persist(toKeep)
      
      return removed
    } catch (error) {
      console.error('Failed to clear old suggestions:', error)
      return 0
    }
  }

  /**
   * 导出建议为 JSON
   */
  static export(): string {
    try {
      return JSON.stringify(this.getAll(), null, 2)
    } catch (error) {
      console.error('Failed to export suggestions:', error)
      return '[]'
    }
  }

  /**
   * 从 JSON 导入建议
   */
  static import(json: string): boolean {
    try {
      const imported = JSON.parse(json)
      if (!Array.isArray(imported)) return false
      
      const all = this.getAll()
      const newSuggestions = imported.filter(s => !all.some(e => this.generateHash(e) === this.generateHash(s)))
      
      this.persist([...newSuggestions, ...all].slice(0, this.MAX_ITEMS))
      
      return true
    } catch (error) {
      console.error('Failed to import suggestions:', error)
      return false
    }
  }

  /**
   * 获取存储统计信息
   */
  static getStats() {
    const all = this.getAll()
    
    return {
      total: all.length,
      favorites: all.filter(s => s.isFavorite).length,
      workflows: all.filter(s => s.type === 'workflow').length,
      nodes: all.filter(s => s.type === 'node').length,
      oldestTimestamp: all.length > 0 ? Math.min(...all.map(s => s.timestamp)) : 0,
      newestTimestamp: all.length > 0 ? Math.max(...all.map(s => s.timestamp)) : 0,
      storageSize: this.getStorageSize(),
    }
  }

  /**
   * 私有方法：生成内容哈希（用于去重）
   */
  private static generateHash(suggestion: StoredSuggestion): string {
    try {
      const content = JSON.stringify({
        type: suggestion.type,
        content: suggestion.content,
      })
      
      // 简单哈希函数
      let hash = 0
      for (let i = 0; i < content.length; i++) {
        const char = content.charCodeAt(i)
        hash = ((hash << 5) - hash) + char
        hash = hash & hash // Convert to 32bit integer
      }
      
      return hash.toString(36)
    } catch {
      return `${suggestion.type}-${suggestion.id}`
    }
  }

  /**
   * 私有方法：持久化到存储
   */
  private static persist(suggestions: StoredSuggestion[]): void {
    try {
      localStorage.setItem(
        this.STORAGE_KEY,
        JSON.stringify(suggestions)
      )
    } catch (error) {
      console.error('Storage quota exceeded:', error)
      // 尝试清除旧项
      const cleaned = suggestions.filter(s => s.isFavorite)
      if (cleaned.length > 0) {
        localStorage.setItem(this.STORAGE_KEY, JSON.stringify(cleaned))
      }
    }
  }

  /**
   * 私有方法：获取存储大小（字节）
   */
  private static getStorageSize(): number {
    try {
      const stored = localStorage.getItem(this.STORAGE_KEY) || ''
      return new Blob([stored]).size
    } catch {
      return 0
    }
  }
}

/**
 * React Hook：使用建议存储
 */
export function useSuggestionStorage() {
  const save = (suggestion: StoredSuggestion) => {
    SuggestionStorage.saveSuggestion(suggestion)
  }

  const getAll = () => {
    return SuggestionStorage.getAll()
  }

  const getFavorites = () => {
    return SuggestionStorage.getFavorites()
  }

  const toggleFavorite = (id: string) => {
    return SuggestionStorage.toggleFavorite(id)
  }

  const search = (filter: SuggestionFilter) => {
    return SuggestionStorage.search(filter)
  }

  const remove = (id: string) => {
    return SuggestionStorage.removeSuggestion(id)
  }

  const clear = () => {
    SuggestionStorage.clear()
  }

  const getStats = () => {
    return SuggestionStorage.getStats()
  }

  return {
    save,
    getAll,
    getFavorites,
    toggleFavorite,
    search,
    remove,
    clear,
    getStats,
  }
}

export default SuggestionStorage
