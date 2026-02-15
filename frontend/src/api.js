/**
 * @fileoverview HTTP + SSE client for the LLM Council backend API.
 *
 * Provides CRUD operations for conversations and a streaming method that
 * consumes Server-Sent Events (SSE) to progressively deliver the 3-stage
 * council pipeline results to the UI.
 *
 * Cliente HTTP + SSE para la API del backend LLM Council.
 * Provee operaciones CRUD para conversaciones y un método de streaming
 * que consume SSE para entregar progresivamente los resultados del
 * pipeline de 3 etapas a la UI.
 *
 * @module api
 */

/** @constant {string} Base URL for the FastAPI backend (default dev port). */
const API_BASE = 'http://localhost:8001';

export const api = {
  /**
   * Fetch metadata for all conversations (id, title, message_count).
   * @returns {Promise<Array<{id: string, title: string, message_count: number}>>}
   */
  async listConversations() {
    const response = await fetch(`${API_BASE}/api/conversations`);
    if (!response.ok) {
      throw new Error('Failed to list conversations');
    }
    return response.json();
  },

  /**
   * Create a new empty conversation on the backend.
   * @returns {Promise<{id: string, created_at: string, title: string, messages: Array}>}
   */
  async createConversation() {
    const response = await fetch(`${API_BASE}/api/conversations`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({}),
    });
    if (!response.ok) {
      throw new Error('Failed to create conversation');
    }
    return response.json();
  },

  /**
   * Load a full conversation (with all messages and stage data).
   * @param {string} conversationId - UUID of the conversation to retrieve.
   * @returns {Promise<Object>} Full conversation payload.
   */
  async getConversation(conversationId) {
    const response = await fetch(
      `${API_BASE}/api/conversations/${conversationId}`
    );
    if (!response.ok) {
      throw new Error('Failed to get conversation');
    }
    return response.json();
  },

  /**
   * Send a message and wait for the complete 3-stage result (non-streaming).
   * @param {string} conversationId - Target conversation UUID.
   * @param {string} content - User's question text.
   * @returns {Promise<{stage1: Array, stage2: Array, stage3: Object, metadata: Object}>}
   */
  async sendMessage(conversationId, content) {
    const response = await fetch(
      `${API_BASE}/api/conversations/${conversationId}/message`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ content }),
      }
    );
    if (!response.ok) {
      throw new Error('Failed to send message');
    }
    return response.json();
  },

  /**
   * Send a message and consume the SSE stream for real-time progress.
   *
   * Opens a long-lived POST request to the ``/message/stream`` endpoint and
   * reads ``text/event-stream`` chunks. Each parsed event is forwarded to
   * the ``onEvent`` callback so the UI can update progressively.
   *
   * @param {string} conversationId - Target conversation UUID.
   * @param {string} content - User's question text.
   * @param {(eventType: string, event: Object) => void} onEvent
   *   Callback invoked for every SSE event. ``eventType`` is one of:
   *   ``stage1_start``, ``stage1_retry``, ``stage1_complete``,
   *   ``stage2_start``, ``stage2_complete``,
   *   ``stage3_start``, ``stage3_retry``, ``stage3_complete``,
   *   ``title_complete``, ``complete``, ``error``.
   * @param {Object} [modelConfig={}] - Optional ``{council_models, chairman_model}`` overrides.
   * @returns {Promise<void>} Resolves when the stream closes.
   */
  async sendMessageStream(conversationId, content, onEvent, modelConfig = {}) {
    const response = await fetch(
      `${API_BASE}/api/conversations/${conversationId}/message/stream`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ content, ...modelConfig }),
      }
    );

    if (!response.ok) {
      throw new Error('Failed to send message');
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const parts = buffer.split('\n\n');
      // Keep the last (potentially incomplete) part in the buffer
      buffer = parts.pop() || '';

      for (const part of parts) {
        for (const line of part.split('\n')) {
          if (line.startsWith('data: ')) {
            try {
              const event = JSON.parse(line.slice(6));
              onEvent(event.type, event);
            } catch (e) {
              console.error('Failed to parse SSE event:', e);
            }
          }
        }
      }
    }
  },
};
