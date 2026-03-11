/**
 * AI Chat API
 * Conversational AI interface for estimation assistance
 */

import { apiClient } from './client';

export interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp?: string;
}

export interface ChatRequest {
  messages: ChatMessage[];
  model?: string;
  context?: {
    estimateId?: string;
    quoteId?: string;
    customerId?: string;
  };
  options?: {
    temperature?: number;
    maxTokens?: number;
    stream?: boolean;
  };
}

export interface ChatResponse {
  message: ChatMessage;
  usage?: {
    promptTokens: number;
    completionTokens: number;
    totalTokens: number;
  };
  model: string;
  suggestions?: string[];
  relatedActions?: Array<{
    type: string;
    label: string;
    data?: Record<string, unknown>;
  }>;
}

export interface AiModel {
  id: string;
  name: string;
  description?: string;
  maxTokens?: number;
  capabilities: string[];
}

export interface AiIntent {
  intent: string;
  confidence: number;
  entities?: Record<string, unknown>;
  suggestedAction?: {
    type: string;
    data: Record<string, unknown>;
  };
}

/**
 * Send chat message to AI
 */
export async function sendChatMessage(
  request: ChatRequest,
  signal?: AbortSignal
): Promise<ChatResponse> {
  return apiClient.post<ChatResponse>('/v1/ai/chat', request, { signal });
}

/**
 * Stream chat message (Server-Sent Events)
 */
export async function* streamChatMessage(
  request: ChatRequest,
  signal?: AbortSignal
): AsyncGenerator<ChatResponse, void, unknown> {
  const response = await fetch(`${apiClient['baseUrl']}/v1/ai/chat/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'text/event-stream',
    },
    body: JSON.stringify({ ...request, options: { ...request.options, stream: true } }),
    signal,
  });

  if (!response.ok) {
    throw new Error(`Chat stream failed: ${response.statusText}`);
  }

  const reader = response.body?.getReader();
  if (!reader) {
    throw new Error('Response body is not readable');
  }

  const decoder = new TextDecoder();
  let buffer = '';

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6);
          if (data === '[DONE]') {
            return;
          }

          try {
            const parsed = JSON.parse(data);
            yield parsed as ChatResponse;
          } catch (e) {
            console.error('Failed to parse SSE data:', e);
          }
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
}

/**
 * Get available AI models
 */
export async function getAiModels(signal?: AbortSignal): Promise<AiModel[]> {
  return apiClient.get<AiModel[]>('/v1/ai/models', { signal });
}

/**
 * Detect intent from user message
 */
export async function detectIntent(
  message: string,
  context?: {
    estimateId?: string;
    quoteId?: string;
  },
  signal?: AbortSignal
): Promise<AiIntent> {
  return apiClient.post<AiIntent>(
    '/v1/ai/intents',
    { message, context },
    { signal }
  );
}

/**
 * Get AI suggestions for estimate
 */
export async function getEstimateSuggestions(
  estimateId: string,
  signal?: AbortSignal
): Promise<{
  suggestions: Array<{
    type: string;
    message: string;
    data?: Record<string, unknown>;
  }>;
}> {
  return apiClient.get<{
    suggestions: Array<{
      type: string;
      message: string;
      data?: Record<string, unknown>;
    }>;
  }>(`/v1/ai/suggestions/estimate/${estimateId}`, { signal });
}

/**
 * Get AI optimization recommendations
 */
export async function getOptimizationRecommendations(
  estimateId: string,
  signal?: AbortSignal
): Promise<{
  recommendations: Array<{
    type: 'cost' | 'efficiency' | 'quality';
    message: string;
    impact: 'low' | 'medium' | 'high';
    data?: Record<string, unknown>;
  }>;
}> {
  return apiClient.get<{
    recommendations: Array<{
      type: 'cost' | 'efficiency' | 'quality';
      message: string;
      impact: 'low' | 'medium' | 'high';
      data?: Record<string, unknown>;
    }>;
  }>(`/v1/ai/optimize/${estimateId}`, { signal });
}

/**
 * Get AI help for error message
 */
export async function getErrorHelp(
  errorCode: string,
  errorMessage: string,
  signal?: AbortSignal
): Promise<{
  explanation: string;
  solutions: string[];
  relatedDocs?: string[];
}> {
  return apiClient.post<{
    explanation: string;
    solutions: string[];
    relatedDocs?: string[];
  }>(
    '/v1/ai/help/error',
    { errorCode, errorMessage },
    { signal }
  );
}

/**
 * Clear chat history
 */
export async function clearChatHistory(
  sessionId?: string,
  signal?: AbortSignal
): Promise<{ cleared: boolean }> {
  return apiClient.post<{ cleared: boolean }>(
    '/v1/ai/chat/clear',
    { sessionId },
    { signal }
  );
}
