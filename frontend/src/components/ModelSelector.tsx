'use client';

import React, { useEffect, useState } from 'react';
import { getAvailableLLMConfigs, LLMConfig } from '@/services/llm-config-client';

interface ModelSelectorProps {
  selectedModelId?: string;
  onModelSelect?: (modelId: string, model: LLMConfig) => void;
  showLabel?: boolean;
  className?: string;
}

/**
 * Model Selector Component
 * Displays available LLM configurations for user selection
 */
export const ModelSelector: React.FC<ModelSelectorProps> = ({
  selectedModelId,
  onModelSelect,
  showLabel = true,
  className = '',
}) => {
  const [models, setModels] = useState<LLMConfig[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadModels = async () => {
      try {
        setLoading(true);
        const availableModels = await getAvailableLLMConfigs();
        setModels(availableModels);
        setError(null);

        // Auto-select first model if none selected
        if (!selectedModelId && availableModels.length > 0) {
          onModelSelect?.(availableModels[0].id, availableModels[0]);
        }
      } catch (err) {
        console.error('Failed to load LLM models:', err);
        setError('Failed to load available models');
      } finally {
        setLoading(false);
      }
    };

    loadModels();
  }, [selectedModelId, onModelSelect]);

  const handleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const modelId = e.target.value;
    const selectedModel = models.find((m) => m.id === modelId);
    if (selectedModel) {
      onModelSelect?.(modelId, selectedModel);
    }
  };

  if (loading) {
    return <div className={`text-gray-500 ${className}`}>Loading models...</div>;
  }

  if (error) {
    return <div className={`text-red-500 ${className}`}>{error}</div>;
  }

  if (models.length === 0) {
    return <div className={`text-gray-500 ${className}`}>No models available</div>;
  }

  return (
    <div className={`flex flex-col gap-2 ${className}`}>
      {showLabel && <label className="text-sm font-medium text-gray-700">AI Model</label>}
      <select
        value={selectedModelId || models[0]?.id || ''}
        onChange={handleChange}
        className="px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
      >
        {models.map((model) => (
          <option key={model.id} value={model.id}>
            {model.display_name} ({model.provider})
          </option>
        ))}
      </select>
    </div>
  );
};

export default ModelSelector;
