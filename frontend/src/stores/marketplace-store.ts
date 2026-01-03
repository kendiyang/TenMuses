import { create } from 'zustand';
import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface Template {
  id: string;
  name: string;
  description: string;
  category: string;
  tags?: string[];
  icon_url?: string;
  author_id: string;
  use_count: number;
  favorite_count: number;
  rating: number;
  is_featured: boolean;
  created_at: string;
}

interface MarketplaceState {
  // Data
  templates: Template[];
  filteredTemplates: Template[];
  featuredTemplates: Template[];
  userFavorites: string[]; // Template IDs of user's favorites
  categories: string[];
  selectedTags: string[];
  
  // Filters
  searchQuery: string;
  selectedCategory: string | null;
  sortBy: 'popular' | 'recent' | 'rating';
  
  // Loading states
  isLoadingTemplates: boolean;
  isLoadingFeatured: boolean;
  isLoadingFavorites: boolean;
  favoriteLoadingIds: Set<string>;
  
  // Error states
  templatesError: string | null;
  
  // Pagination
  page: number;
  pageSize: number;
  totalCount: number;
  totalPages: number;
  
  // Actions
  fetchTemplates: (params?: { category?: string; tags?: string[]; search?: string; sort?: string; page?: number }) => Promise<void>;
  fetchFeaturedTemplates: () => Promise<void>;
  fetchUserFavorites: () => Promise<void>;
  toggleFavorite: (templateId: string) => Promise<void>;
  isFavorited: (templateId: string) => boolean;
  setSearchQuery: (query: string) => void;
  setSelectedCategory: (category: string | null) => void;
  setSortBy: (sort: 'popular' | 'recent' | 'rating') => void;
  setPage: (page: number) => void;
  setPageSize: (size: number) => void;
  addTag: (tag: string) => void;
  removeTag: (tag: string) => void;
  clearFilters: () => void;
  reset: () => void;
}

const initialState = {
  templates: [],
  filteredTemplates: [],
  featuredTemplates: [],
  userFavorites: [],
  categories: ['Data Analysis', 'Content Creation', 'Business', 'Marketing', 'Development'],
  selectedTags: [],
  searchQuery: '',
  selectedCategory: null,
  sortBy: 'popular' as const,
  isLoadingTemplates: false,
  isLoadingFeatured: false,
  isLoadingFavorites: false,
  favoriteLoadingIds: new Set<string>(),
  templatesError: null,
  page: 1,
  pageSize: 20,
  totalCount: 0,
  totalPages: 1,
};

export const useMarketplaceStore = create<MarketplaceState>((set, get) => ({
  ...initialState,

  fetchTemplates: async (params = {}) => {
    set({ isLoadingTemplates: true, templatesError: null });
    
    try {
      const token = localStorage.getItem('accessToken');
      if (!token) {
        throw new Error('No access token found');
      }

      const {
        category = get().selectedCategory,
        tags = get().selectedTags,
        search = get().searchQuery,
        sort = get().sortBy,
        page = get().page
      } = params;

      const queryParams = new URLSearchParams();
      if (category) queryParams.append('category', category);
      if (tags?.length) queryParams.append('tags', tags.join(','));
      if (search) queryParams.append('search', search);
      queryParams.append('sort_by', sort);
      queryParams.append('page', String(page));
      queryParams.append('page_size', String(get().pageSize));

      const response = await axios.get(
        `${API_URL}/api/v1/marketplace/templates?${queryParams}`,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      // 后端返回 PaginatedTemplateResponse 格式
      set({
        templates: response.data.items || [],
        totalCount: response.data.total || 0,
        totalPages: response.data.total_pages || 1,
        page: response.data.page || 1,
        isLoadingTemplates: false,
      });
    } catch (error: any) {
      console.error('Failed to fetch templates:', error);
      set({
        templatesError: error.response?.data?.detail || error.message || 'Failed to load templates',
        isLoadingTemplates: false,
      });
    }
  },

  fetchFeaturedTemplates: async () => {
    set({ isLoadingFeatured: true });
    
    try {
      const token = localStorage.getItem('accessToken');
      if (!token) {
        throw new Error('No access token found');
      }

      const response = await axios.get(
        `${API_URL}/api/v1/marketplace/templates/featured?limit=8`,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      set({
        featuredTemplates: response.data || [],
        isLoadingFeatured: false,
      });
    } catch (error) {
      console.error('Failed to fetch featured templates:', error);
      set({ isLoadingFeatured: false });
    }
  },

  setSearchQuery: (query: string) => {
    set({ searchQuery: query, page: 1 });
    get().fetchTemplates({ search: query });
  },

  setSelectedCategory: (category: string | null) => {
    set({ selectedCategory: category, page: 1 });
    get().fetchTemplates({ category });
  },

  setSortBy: (sort: 'popular' | 'recent' | 'rating') => {
    set({ sortBy: sort, page: 1 });
    get().fetchTemplates({ sort });
  },

  addTag: (tag: string) => {
    const currentTags = get().selectedTags;
    if (!currentTags.includes(tag)) {
      const newTags = [...currentTags, tag];
      set({ selectedTags: newTags, page: 1 });
      get().fetchTemplates({ tags: newTags });
    }
  },

  removeTag: (tag: string) => {
    const newTags = get().selectedTags.filter(t => t !== tag);
    set({ selectedTags: newTags, page: 1 });
    get().fetchTemplates({ tags: newTags });
  },

  clearFilters: () => {
    set({
      searchQuery: '',
      selectedCategory: null,
      selectedTags: [],
      sortBy: 'popular',
      page: 1,
    });
    get().fetchTemplates();
  },

  setPage: (page: number) => {
    set({ page });
    get().fetchTemplates({ page });
  },

  setPageSize: (size: number) => {
    set({ pageSize: size, page: 1 });
    get().fetchTemplates({ page: 1 });
  },

  fetchUserFavorites: async () => {
    set({ isLoadingFavorites: true });
    
    try {
      const token = localStorage.getItem('accessToken');
      if (!token) {
        throw new Error('No access token found');
      }

      const response = await axios.get(
        `${API_URL}/api/v1/marketplace/favorites`,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      const favoriteIds = (response.data || []).map((t: Template) => t.id);
      set({
        userFavorites: favoriteIds,
        isLoadingFavorites: false,
      });
    } catch (error) {
      console.error('Failed to fetch favorites:', error);
      set({ isLoadingFavorites: false });
    }
  },

  toggleFavorite: async (templateId: string) => {
    const isFavorited = get().userFavorites.includes(templateId);
    const token = localStorage.getItem('accessToken');
    
    if (!token) {
      throw new Error('No access token found');
    }

    try {
      set((state) => ({
        favoriteLoadingIds: new Set(state.favoriteLoadingIds).add(templateId),
      }));

      if (isFavorited) {
        // Remove from favorites
        await axios.delete(
          `${API_URL}/api/v1/marketplace/templates/${templateId}/favorite`,
          {
            headers: { Authorization: `Bearer ${token}` },
          }
        );

        set((state) => ({
          userFavorites: state.userFavorites.filter(id => id !== templateId),
          templates: state.templates.map(t => 
            t.id === templateId ? { ...t, favorite_count: Math.max(0, t.favorite_count - 1) } : t
          ),
        }));
      } else {
        // Add to favorites
        await axios.post(
          `${API_URL}/api/v1/marketplace/templates/${templateId}/favorite`,
          {},
          {
            headers: { Authorization: `Bearer ${token}` },
          }
        );

        set((state) => ({
          userFavorites: [...state.userFavorites, templateId],
          templates: state.templates.map(t => 
            t.id === templateId ? { ...t, favorite_count: t.favorite_count + 1 } : t
          ),
        }));
      }
    } catch (error) {
      console.error('Failed to toggle favorite:', error);
      throw error;
    } finally {
      set((state) => {
        const newSet = new Set(state.favoriteLoadingIds);
        newSet.delete(templateId);
        return { favoriteLoadingIds: newSet };
      });
    }
  },

  isFavorited: (templateId: string) => {
    return get().userFavorites.includes(templateId);
  },

  reset: () => {
    set(initialState);
  },
}));
