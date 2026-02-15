/**
 * @fileoverview Main chat interface — message history + battle visualization.
 *
 * Renders user messages, embeds the ProcessTimeline arena view for each
 * assistant response, provides collapsible detailed-stage views (Stage1,
 * Stage2), and includes the ModelSelector configuration panel with the
 * message input form.
 *
 * Interfaz de chat principal — historial de mensajes + visualización de batalla.
 *
 * @module ChatInterface
 */

import { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import Stage1 from './Stage1';
import Stage2 from './Stage2';
import Stage3 from './Stage3';
import ProcessTimeline from './ProcessTimeline';
import ModelSelector from './ModelSelector';
import './ChatInterface.css';

/**
 * @param {Object} props
 * @param {Object|null} props.conversation - Current conversation (null = welcome screen).
 * @param {(content: string) => Promise<void>} props.onSendMessage - Send user message handler.
 * @param {boolean} props.isLoading - True while a battle is running.
 * @param {(config: Object) => void} props.onModelConfigChange - Model config change callback.
 * @returns {JSX.Element}
 */
export default function ChatInterface({
  conversation,
  onSendMessage,
  isLoading,
  onModelConfigChange,
}) {
  const [input, setInput] = useState('');
  const [showDetails, setShowDetails] = useState({});
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [conversation]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (input.trim() && !isLoading) {
      onSendMessage(input);
      setInput('');
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const toggleDetails = (index) => {
    setShowDetails(prev => ({
      ...prev,
      [index]: !prev[index]
    }));
  };

  if (!conversation) {
    return (
      <div className="chat-interface">
        <div className="empty-state">
          <h2>Bienvenido al Consejo LLM</h2>
          <p>Crea una nueva conversacion para comenzar</p>
        </div>
      </div>
    );
  }

  return (
    <div className="chat-interface">
      <div className="messages-container">
        {conversation.messages.length === 0 ? (
          <div className="empty-state">
            <h2>Inicia una conversacion</h2>
            <p>Haz una pregunta para consultar al Consejo LLM</p>
          </div>
        ) : (
          conversation.messages.map((msg, index) => (
            <div key={index} className="message-group">
              {msg.role === 'user' ? (
                <div className="user-message">
                  <div className="message-label">Tu</div>
                  <div className="message-content">
                    <div className="markdown-content">
                      <ReactMarkdown>{msg.content}</ReactMarkdown>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="assistant-message">
                  <div className="message-label">Consejo LLM</div>

                  {/* ===== PROCESS TIMELINE (BATTLE VIEW) ===== */}
                  <ProcessTimeline message={msg} isLoading={isLoading} />

                  {/* ===== DETAILED STAGES (collapsible) ===== */}
                  {(msg.stage1 || msg.stage2 || msg.stage3) && (
                    <div className="details-toggle-container">
                      <button
                        className="details-toggle-btn"
                        onClick={() => toggleDetails(index)}
                      >
                        {showDetails[index] ? '▼ Ocultar respuestas completas' : '▶ Ver respuestas completas de cada modelo'}
                      </button>
                    </div>
                  )}

                  {showDetails[index] && (
                    <div className="detailed-stages">
                      {msg.stage1 && <Stage1 responses={msg.stage1} />}
                      {msg.stage2 && (
                        <Stage2
                          rankings={msg.stage2}
                          labelToModel={msg.metadata?.label_to_model}
                          aggregateRankings={msg.metadata?.aggregate_rankings}
                        />
                      )}
                    </div>
                  )}

                  {/* Stage 3 is now shown inside ProcessTimeline */}
                </div>
              )}
            </div>
          ))
        )}

        {isLoading && !conversation.messages.some(m => m.role === 'assistant' && m.loading) && (
          <div className="loading-indicator">
            <div className="spinner"></div>
            <span>Consultando al consejo...</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {conversation.messages.length === 0 && (
        <div className="input-area">
          <ModelSelector onConfigChange={onModelConfigChange} disabled={isLoading} />
          <form className="input-form" onSubmit={handleSubmit}>
            <textarea
              className="message-input"
              placeholder="Escribe tu pregunta... (Shift+Enter nueva linea, Enter para enviar)"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={isLoading}
              rows={3}
            />
            <button
              type="submit"
              className="send-button"
              disabled={!input.trim() || isLoading}
            >
              Enviar
            </button>
          </form>
        </div>
      )}
    </div>
  );
}
