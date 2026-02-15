import { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import ChatInterface from './components/ChatInterface';
import { api } from './api';
import './App.css';

function App() {
  const [conversations, setConversations] = useState([]);
  const [currentConversationId, setCurrentConversationId] = useState(null);
  const [currentConversation, setCurrentConversation] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [modelConfig, setModelConfig] = useState({});

  // Load conversations on mount
  useEffect(() => {
    loadConversations();
  }, []);

  // Load conversation details when selected
  useEffect(() => {
    if (currentConversationId) {
      loadConversation(currentConversationId);
    }
  }, [currentConversationId]);

  const loadConversations = async () => {
    try {
      const convs = await api.listConversations();
      setConversations(convs);
    } catch (error) {
      console.error('Failed to load conversations:', error);
    }
  };

  const loadConversation = async (id) => {
    try {
      const conv = await api.getConversation(id);
      setCurrentConversation(conv);
    } catch (error) {
      console.error('Failed to load conversation:', error);
    }
  };

  const handleNewConversation = async () => {
    try {
      const newConv = await api.createConversation();
      setConversations([
        { id: newConv.id, created_at: newConv.created_at, message_count: 0 },
        ...conversations,
      ]);
      setCurrentConversationId(newConv.id);
    } catch (error) {
      console.error('Failed to create conversation:', error);
    }
  };

  const handleSelectConversation = (id) => {
    setCurrentConversationId(id);
  };

  const handleModelConfigChange = (config) => {
    setModelConfig(config);
  };

  const handleSendMessage = async (content) => {
    if (!currentConversationId) return;

    setIsLoading(true);
    try {
      // Optimistically add user message to UI
      const userMessage = { role: 'user', content };
      setCurrentConversation((prev) => ({
        ...prev,
        messages: [...prev.messages, userMessage],
      }));

      // Create a partial assistant message that will be updated progressively
      const assistantMessage = {
        role: 'assistant',
        stage1: null,
        stage2: null,
        stage3: null,
        metadata: null,
        loading: {
          stage1: false,
          stage2: false,
          stage3: false,
        },
      };

      // Add the partial assistant message
      setCurrentConversation((prev) => ({
        ...prev,
        messages: [...prev.messages, assistantMessage],
      }));

      // Send message with streaming
      // Helper: immutably update the last assistant message
      const updateLastMsg = (updater) => {
        setCurrentConversation((prev) => {
          const messages = prev.messages.slice(0, -1);
          const last = prev.messages[prev.messages.length - 1];
          const updated = { ...last, loading: { ...last.loading }, ...updater(last) };
          return { ...prev, messages: [...messages, updated] };
        });
      };

      await api.sendMessageStream(currentConversationId, content, (eventType, event) => {
        switch (eventType) {
          case 'stage1_start':
            updateLastMsg((m) => ({
              selectedModels: modelConfig.council_models || [],
              loading: { ...m.loading, stage1: true },
            }));
            break;

          case 'stage1_retry':
            updateLastMsg(() => ({ retryInfo: event.data }));
            break;

          case 'stage1_complete':
            updateLastMsg((m) => ({ stage1: event.data, retryInfo: null, loading: { ...m.loading, stage1: false } }));
            break;

          case 'stage2_start':
            updateLastMsg((m) => ({ loading: { ...m.loading, stage2: true } }));
            break;

          case 'stage2_complete':
            updateLastMsg((m) => ({ stage2: event.data, metadata: event.metadata, loading: { ...m.loading, stage2: false } }));
            break;

          case 'stage3_start':
            updateLastMsg((m) => ({ loading: { ...m.loading, stage3: true } }));
            break;

          case 'stage3_retry':
            updateLastMsg(() => ({ stage3RetryInfo: event.data }));
            break;

          case 'stage3_complete':
            updateLastMsg((m) => ({ stage3: event.data, stage3RetryInfo: null, loading: { ...m.loading, stage3: false } }));
            break;

          case 'title_complete':
            // Reload conversations to get updated title
            loadConversations();
            break;

          case 'complete':
            // Stream complete, reload conversations list
            loadConversations();
            setIsLoading(false);
            break;

          case 'error':
            console.error('Stream error:', event.message);
            setIsLoading(false);
            break;

          default:
            console.log('Unknown event type:', eventType);
        }
      }, modelConfig);
    } catch (error) {
      console.error('Failed to send message:', error);
      // Remove optimistic messages on error
      setCurrentConversation((prev) => ({
        ...prev,
        messages: prev.messages.slice(0, -2),
      }));
      setIsLoading(false);
    }
  };

  return (
    <div className="app">
      <Sidebar
        conversations={conversations}
        currentConversationId={currentConversationId}
        onSelectConversation={handleSelectConversation}
        onNewConversation={handleNewConversation}
      />
      <ChatInterface
        conversation={currentConversation}
        onSendMessage={handleSendMessage}
        isLoading={isLoading}
        onModelConfigChange={handleModelConfigChange}
      />
    </div>
  );
}

export default App;
