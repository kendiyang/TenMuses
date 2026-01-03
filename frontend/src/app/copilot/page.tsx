'use client';

import React, { useState } from 'react';
import { ModelSelector } from '@/components/ModelSelector';
import { LLMConfig } from '@/services/llm-config-client';
import { copilotClient } from '@/services/copilot-client';
import { Send } from 'lucide-react';

/**
 * Copilot Demo Page
 * Demonstrates model selection and interaction
 */
export default function CopilotPage() {
  const [selectedModel, setSelectedModel] = useState<LLMConfig | null>(null);
  const [messages, setMessages] = useState<{ role: string; content: string }[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  const handleModelSelect = (modelId: string, model: LLMConfig) => {
    setSelectedModel(model);
    console.log('Selected model:', model);
  };

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || !selectedModel || loading) return;

    const userMessage = { role: 'user', content: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      // Call real API instead of mock response
      const response = await copilotClient.chat({
        message: userMessage.content,
        model: selectedModel.model_name,
        chat_history: messages.map((m) => ({
          role: m.role,
          content: m.content,
        })),
      });

      const assistantMessage = {
        role: 'assistant',
        content: response.message,
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Failed to send message:', error);
      // Remove the user message if API call fails
      setMessages((prev) => prev.slice(0, -1));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-8">
      <div className="max-w-4xl mx-auto">
        <div className="bg-white rounded-lg shadow-lg p-8">
          {/* Header */}
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Copilot</h1>
          <p className="text-gray-600 mb-8">Select an AI model and start chatting</p>

          {/* Model Selector */}
          <div className="mb-8 p-4 bg-gray-50 rounded-lg">
            <ModelSelector
              selectedModelId={selectedModel?.id}
              onModelSelect={handleModelSelect}
              showLabel={true}
            />
          </div>

          {/* Messages */}
          <div className="mb-6 h-96 bg-gray-50 rounded-lg p-4 overflow-y-auto border border-gray-200">
            {messages.length === 0 ? (
              <div className="flex items-center justify-center h-full text-gray-500">
                <div className="text-center">
                  <p className="text-lg">No messages yet</p>
                  <p className="text-sm">Select a model and start typing to begin</p>
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                {messages.map((msg, idx) => (
                  <div
                    key={idx}
                    className={`flex ${
                      msg.role === 'user' ? 'justify-end' : 'justify-start'
                    }`}
                  >
                    <div
                      className={`px-4 py-2 rounded-lg max-w-xs ${
                        msg.role === 'user'
                          ? 'bg-blue-500 text-white'
                          : 'bg-gray-200 text-gray-900'
                      }`}
                    >
                      {msg.content}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Input */}
          <form onSubmit={handleSendMessage} className="flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={selectedModel ? 'Type your message...' : 'Select a model first...'}
              disabled={!selectedModel || loading}
              className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 disabled:text-gray-500"
            />
            <button
              type="submit"
              disabled={!selectedModel || loading || !input.trim()}
              className="px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed flex items-center gap-2"
            >
              <Send className="w-5 h-5" />
              {loading ? 'Sending...' : 'Send'}
            </button>
          </form>

          {/* Info */}
          <div className="mt-8 p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <p className="text-sm text-gray-700">
              <strong>Selected Model:</strong>{' '}
              {selectedModel ? (
                <span>
                  {selectedModel.display_name} ({selectedModel.provider} - {selectedModel.model_name})
                </span>
              ) : (
                <span className="text-gray-500">None</span>
              )}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
