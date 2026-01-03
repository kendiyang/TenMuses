import { create } from 'zustand';
import { apiClient } from '@/lib/api-client';

export interface WorkflowSummary {
  id: string;
  title: string;
  description?: string;
  tags?: string[];
  status: 'draft' | 'published' | 'running';
  last_run_at?: string;
  created_at: string;
  updated_at: string;
  nodes_count: number;
}

export interface WorkspaceStatistics {
  total_workflows: number;
  total_runs: number;
  total_templates: number;
}

export interface FeaturedTemplate {
  id: string;
  name: string;
  description: string;
  category: string;
  tags?: string[];
  icon_url?: string;
  rating: number;
  use_count: number;
  favorite_count: number;
}

interface WorkspaceState {
  // Data
  recentWorkflows: WorkflowSummary[];
  statistics: WorkspaceStatistics | null;
  featuredTemplates: FeaturedTemplate[];
  
  // Loading states
  isLoadingOverview: boolean;
  isLoadingRecent: boolean;
  
  // Error states
  overviewError: string | null;
  recentError: string | null;
  
  // Actions
  fetchWorkspaceOverview: () => Promise<void>;
  fetchRecentWorkflows: (limit?: number) => Promise<void>;
  refresh: () => Promise<void>;
  reset: () => void;
}

const initialState = {
  recentWorkflows: [],
  statistics: null,
  featuredTemplates: [],
  isLoadingOverview: false,
  isLoadingRecent: false,
  overviewError: null,
  recentError: null,
};

export const useWorkspaceStore = create<WorkspaceState>((set, get) => ({
  ...initialState,

  fetchWorkspaceOverview: async () => {
    set({ isLoadingOverview: true, overviewError: null });
    
    try {
      const data = await apiClient.get<any>('/workspace');
      
      set({
        recentWorkflows: data.recent_workflows || [],
        statistics: data.statistics || null,
        featuredTemplates: data.featured_templates || [],
        isLoadingOverview: false,
      });
    } catch (error: any) {
      console.error('Failed to fetch workspace overview:', error);
      set({
        overviewError: error.response?.data?.detail || error.message || 'Failed to load workspace overview',
        isLoadingOverview: false,
      });
    }
  },

  fetchRecentWorkflows: async (limit = 10) => {
    set({ isLoadingRecent: true, recentError: null });
    
    try {
      const data = await apiClient.get<any>('/workspace/recent', { limit });

      set({
        recentWorkflows: data || [],
        isLoadingRecent: false,
      });
    } catch (error: any) {
      console.error('Failed to fetch recent workflows:', error);
      set({
        recentError: error.response?.data?.detail || error.message || 'Failed to load recent workflows',
        isLoadingRecent: false,
      });
    }
  },

  refresh: async () => {
    await Promise.all([
      get().fetchWorkspaceOverview(),
      get().fetchRecentWorkflows(),
    ]);
  },

  reset: () => {
    set(initialState);
  },
}));
