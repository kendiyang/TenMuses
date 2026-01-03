/**
 * LLM Configuration Client Service
 * Communicates with backend LLM config endpoints
 */

import axios from 'axios';

export interface LLMConfig {
  id: string;
  provider: string;
  model_name: string;
  display_name: string;
  priority: number;
}

export interface LLMConfigDetail extends LLMConfig {
  base_url?: string;
  is_active: boolean;
  description?: string;
  api_key?: string;
  created_at: string;
  updated_at: string;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const API_BASE = `${API_URL}/api/v1`;

const axiosInstance = axios.create({
  baseURL: API_BASE,
});

// Add auth token to requests
axiosInstance.interceptors.request.use((config) => {
  const token = localStorage.getItem('accessToken');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

/**
 * Get list of active LLM configurations for user selection
 */
export async function getAvailableLLMConfigs(): Promise<LLMConfig[]> {
  try {
    const response = await axiosInstance.get('/llm-config/models', {
      params: { active_only: true },
    });
    return response.data.sort((a: LLMConfig, b: LLMConfig) => a.priority - b.priority);
  } catch (error) {
    console.error('Failed to fetch available LLM configs:', error);
    return [];
  }
}

/**
 * Get all LLM configurations with details (admin only)
 */
export async function getAllLLMConfigs(): Promise<LLMConfigDetail[]> {
  try {
    const response = await axiosInstance.get('/llm-configs/admin');
    return response.data.sort((a: LLMConfigDetail, b: LLMConfigDetail) => a.priority - b.priority);
  } catch (error) {
    console.error('Failed to fetch all LLM configs:', error);
    throw error;
  }
}

/**
 * Create new LLM configuration (admin only)
 */
export async function createLLMConfig(config: {
  provider: string;
  model_name: string;
  display_name: string;
  api_key: string;
  base_url?: string;
  priority?: number;
  description?: string;
}): Promise<LLMConfigDetail> {
  try {
    const response = await axiosInstance.post('/llm-configs', config);
    return response.data;
  } catch (error) {
    console.error('Failed to create LLM config:', error);
    throw error;
  }
}

/**
 * Update LLM configuration (admin only)
 */
export async function updateLLMConfig(
  configId: string,
  updates: Partial<{
    model_name: string;
    display_name: string;
    api_key: string;
    base_url: string;
    is_active: boolean;
    priority: number;
    description: string;
  }>
): Promise<LLMConfigDetail> {
  try {
    const response = await axiosInstance.put(`/llm-configs/${configId}`, updates);
    return response.data;
  } catch (error) {
    console.error(`Failed to update LLM config ${configId}:`, error);
    throw error;
  }
}

/**
 * Delete LLM configuration (admin only)
 */
export async function deleteLLMConfig(configId: string): Promise<void> {
  try {
    await axiosInstance.delete(`/llm-configs/${configId}`);
  } catch (error) {
    console.error(`Failed to delete LLM config ${configId}:`, error);
    throw error;
  }
}
