'use client';

import React, { useEffect, useState } from 'react';
import {
  getAllLLMConfigs,
  createLLMConfig,
  updateLLMConfig,
  deleteLLMConfig,
  LLMConfigDetail,
} from '@/services/llm-config-client';

/**
 * LLM Configuration Management Page
 * Admin-only page for managing LLM configurations
 */
export default function LLMConfigPage() {
  const [configs, setConfigs] = useState<LLMConfigDetail[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    provider: 'openai',
    model_name: '',
    display_name: '',
    api_key: '',
    base_url: '',
    priority: 100,
    description: '',
  });

  useEffect(() => {
    loadConfigs();
  }, []);

  const loadConfigs = async () => {
    try {
      setLoading(true);
      const data = await getAllLLMConfigs();
      setConfigs(data);
      setError(null);
    } catch (err) {
      console.error('Failed to load configs:', err);
      setError('Failed to load LLM configurations');
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>
  ) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: name === 'priority' ? parseInt(value) : value,
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editingId) {
        await updateLLMConfig(editingId, formData);
      } else {
        await createLLMConfig(formData);
      }
      setShowForm(false);
      setEditingId(null);
      setFormData({
        provider: 'openai',
        model_name: '',
        display_name: '',
        api_key: '',
        base_url: '',
        priority: 100,
        description: '',
      });
      await loadConfigs();
    } catch (err) {
      console.error('Failed to save config:', err);
      setError('Failed to save configuration');
    }
  };

  const handleEdit = (config: LLMConfigDetail) => {
    setEditingId(config.id);
    setFormData({
      provider: config.provider,
      model_name: config.model_name,
      display_name: config.display_name,
      api_key: config.api_key || '',
      base_url: config.base_url || '',
      priority: config.priority,
      description: config.description || '',
    });
    setShowForm(true);
  };

  const handleDelete = async (configId: string) => {
    if (confirm('Are you sure you want to delete this configuration?')) {
      try {
        await deleteLLMConfig(configId);
        await loadConfigs();
      } catch (err) {
        console.error('Failed to delete config:', err);
        setError('Failed to delete configuration');
      }
    }
  };

  const handleCancel = () => {
    setShowForm(false);
    setEditingId(null);
    setFormData({
      provider: 'openai',
      model_name: '',
      display_name: '',
      api_key: '',
      base_url: '',
      priority: 100,
      description: '',
    });
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-6xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900">LLM Configuration</h1>
          <button
            onClick={() => {
              setEditingId(null);
              setShowForm(!showForm);
            }}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            {showForm && !editingId ? 'Cancel' : 'Add Configuration'}
          </button>
        </div>

        {error && (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
            {error}
          </div>
        )}

        {showForm && (
          <div className="mb-8 p-6 bg-white rounded-lg shadow">
            <h2 className="text-xl font-semibold mb-4">
              {editingId ? 'Edit Configuration' : 'Add New Configuration'}
            </h2>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Provider</label>
                  <select
                    name="provider"
                    value={formData.provider}
                    onChange={handleInputChange}
                    className="mt-1 px-3 py-2 border border-gray-300 rounded-md w-full"
                  >
                    <option value="openai">OpenAI</option>
                    <option value="anthropic">Anthropic</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Model Name</label>
                  <input
                    type="text"
                    name="model_name"
                    value={formData.model_name}
                    onChange={handleInputChange}
                    placeholder="e.g., gpt-4-turbo-preview"
                    required
                    className="mt-1 px-3 py-2 border border-gray-300 rounded-md w-full"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Display Name</label>
                <input
                  type="text"
                  name="display_name"
                  value={formData.display_name}
                  onChange={handleInputChange}
                  placeholder="e.g., GPT-4 Turbo"
                  required
                  className="mt-1 px-3 py-2 border border-gray-300 rounded-md w-full"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">API Key</label>
                <input
                  type="password"
                  name="api_key"
                  value={formData.api_key}
                  onChange={handleInputChange}
                  placeholder="Your API key"
                  required={!editingId}
                  className="mt-1 px-3 py-2 border border-gray-300 rounded-md w-full"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Base URL</label>
                  <input
                    type="text"
                    name="base_url"
                    value={formData.base_url}
                    onChange={handleInputChange}
                    placeholder="Optional custom base URL"
                    className="mt-1 px-3 py-2 border border-gray-300 rounded-md w-full"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Priority</label>
                  <input
                    type="number"
                    name="priority"
                    value={formData.priority}
                    onChange={handleInputChange}
                    className="mt-1 px-3 py-2 border border-gray-300 rounded-md w-full"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Description</label>
                <textarea
                  name="description"
                  value={formData.description}
                  onChange={handleInputChange}
                  placeholder="Optional description"
                  rows={3}
                  className="mt-1 px-3 py-2 border border-gray-300 rounded-md w-full"
                />
              </div>

              <div className="flex gap-2 pt-4">
                <button
                  type="submit"
                  className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
                >
                  {editingId ? 'Update' : 'Create'}
                </button>
                <button
                  type="button"
                  onClick={handleCancel}
                  className="px-4 py-2 bg-gray-300 text-gray-700 rounded-lg hover:bg-gray-400"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        )}

        {loading ? (
          <div className="text-center py-8 text-gray-500">Loading configurations...</div>
        ) : configs.length === 0 ? (
          <div className="text-center py-8 text-gray-500">No configurations found</div>
        ) : (
          <div className="grid gap-4">
            {configs.map((config) => (
              <div
                key={config.id}
                className="p-6 bg-white rounded-lg shadow hover:shadow-lg transition"
              >
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">{config.display_name}</h3>
                    <p className="text-sm text-gray-600">
                      {config.provider} • {config.model_name}
                    </p>
                  </div>
                  <span
                    className={`px-3 py-1 rounded-full text-sm font-medium ${
                      config.is_active
                        ? 'bg-green-100 text-green-800'
                        : 'bg-gray-100 text-gray-800'
                    }`}
                  >
                    {config.is_active ? 'Active' : 'Inactive'}
                  </span>
                </div>

                {config.description && (
                  <p className="text-sm text-gray-600 mb-3">{config.description}</p>
                )}

                <div className="text-xs text-gray-500 mb-4">
                  {config.base_url && <p>Base URL: {config.base_url}</p>}
                  <p>Priority: {config.priority}</p>
                  <p>Created: {new Date(config.created_at).toLocaleDateString()}</p>
                </div>

                <div className="flex gap-2">
                  <button
                    onClick={() => handleEdit(config)}
                    className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700"
                  >
                    Edit
                  </button>
                  <button
                    onClick={() => handleDelete(config.id)}
                    className="px-3 py-1 bg-red-600 text-white text-sm rounded hover:bg-red-700"
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
