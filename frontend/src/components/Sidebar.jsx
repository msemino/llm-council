/**
 * @fileoverview Sidebar navigation — conversation list and creation button.
 *
 * Displays the "Consejo LLM" branding, a "+ Nueva Conversacion" button,
 * and a scrollable list of past conversations with title and message count.
 *
 * Barra lateral de navegación — lista de conversaciones y botón de creación.
 *
 * @module Sidebar
 */

import { useState, useEffect } from 'react';
import './Sidebar.css';

/**
 * @param {Object} props
 * @param {Array<{id: string, title: string, message_count: number}>} props.conversations
 * @param {string|null} props.currentConversationId - Highlighted conversation.
 * @param {(id: string) => void} props.onSelectConversation
 * @param {() => void} props.onNewConversation
 * @returns {JSX.Element}
 */
export default function Sidebar({
  conversations,
  currentConversationId,
  onSelectConversation,
  onNewConversation,
}) {
  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <h1>Consejo LLM ⚔️</h1>
        <button className="new-conversation-btn" onClick={onNewConversation}>
          + Nueva Conversacion
        </button>
      </div>

      <div className="conversation-list">
        {conversations.length === 0 ? (
          <div className="no-conversations">Sin conversaciones aun</div>
        ) : (
          conversations.map((conv) => (
            <div
              key={conv.id}
              className={`conversation-item ${
                conv.id === currentConversationId ? 'active' : ''
              }`}
              onClick={() => onSelectConversation(conv.id)}
            >
              <div className="conversation-title">
                {conv.title || 'Nueva Conversacion'}
              </div>
              <div className="conversation-meta">
                {conv.message_count} mensajes
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
