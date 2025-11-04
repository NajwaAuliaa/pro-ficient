import { createContext, useContext, useState } from "react";

const ChatContext = createContext();

const createMessage = (role, content) => ({
  role,
  content,
  timestamp: new Date().toISOString(),
});

const DEFAULT_MESSAGES = {
  rag: [
    createMessage(
      "assistant",
      "Welcome to Document Assistant. I can help you search and analyze your internal documents."
    ),
  ],
  project: [
    createMessage(
      "assistant",
      "Project Management Assistant ready. I can help with project progress tracking, analysis, and reporting."
    ),
  ],
  todo: [
    createMessage(
      "assistant",
      "Task Management Assistant ready. I can help you create, manage, and track your tasks."
    ),
  ],
};

export const ChatProvider = ({ children }) => {
  // ❌ REMOVE localStorage persistence
  // Chat history will be loaded from backend Memory Manager instead
  const [allMessages, setAllMessages] = useState(DEFAULT_MESSAGES);

  // ❌ REMOVED: localStorage sync
  // Chat persistence is now handled by backend (Cosmos DB + Redis)

  const getMessages = (type) => allMessages[type] || [];
  const setMessages = (type, newMessages) => {
    setAllMessages((prev) => ({
      ...prev,
      [type]: Array.isArray(newMessages)
        ? newMessages.map((msg) => ({
            ...msg,
            role: msg.role || msg.type || "assistant",
            content: msg.content || "",
            timestamp: msg.timestamp || new Date().toISOString(),
          }))
        : [],
    }));
  };

  // Clear specific module chat history
  const clearMessages = (type) => {
    setAllMessages((prev) => ({
      ...prev,
      [type]: DEFAULT_MESSAGES[type],
    }));
  };

  // Clear all chat history (in-memory only, backend data persists)
  const clearAllMessages = () => {
    setAllMessages(DEFAULT_MESSAGES);
    // Note: This only clears frontend state
    // Backend memory (Cosmos DB) is preserved unless explicitly deleted via API
  };

  // Load chat history from backend Memory Manager
  const loadMessagesFromBackend = async (userId, module, limit = 20) => {
    if (!userId || userId === 'null' || userId === 'undefined') {
      console.log('[ChatContext] Cannot load messages: invalid user_id');
      return;
    }

    try {
      const API_BASE = process.env.REACT_APP_API_URL;
      // OPTIMIZED: Reduced limit to 20 for faster initial load (was 100)
      const response = await fetch(`${API_BASE}/memory/history/${userId}?module=${module}&limit=${limit}`);

      if (!response.ok) {
        console.error('[ChatContext] Failed to load history:', response.status);
        return;
      }

      const data = await response.json();

      if (data.history && data.history.length > 0) {
        // Transform backend format to frontend format
        const messages = data.history.map(item => ({
          role: item.role,
          content: item.content,
          timestamp: item.timestamp,
          metadata: item.metadata || {}
        }));

        console.log(`[ChatContext] ✅ Loaded ${messages.length} messages for ${module} from backend (Total in DB: ${data.message_count || messages.length})`);

        setAllMessages(prev => ({
          ...prev,
          [module]: messages
        }));

        return messages.length; // Return count for caller
      } else {
        console.log(`[ChatContext] No history found for ${module}, using defaults`);
        return 0;
      }
    } catch (error) {
      console.error('[ChatContext] Error loading messages from backend:', error);
    }
  };

  return (
    <ChatContext.Provider value={{
      getMessages,
      setMessages,
      clearMessages,
      clearAllMessages,
      loadMessagesFromBackend // Export this for components to use
    }}>
      {children}
    </ChatContext.Provider>
  );
};

// Hook untuk konsumsi
export const useChat = (type) => {
  const context = useContext(ChatContext);
  if (!context) {
    throw new Error("useChat must be used within ChatProvider");
  }

  const { getMessages, setMessages, clearMessages, loadMessagesFromBackend } = context;
  if (!type) throw new Error("❌ useChat harus dipanggil dengan type");

  return {
    messages: getMessages(type),
    setMessages: (msgs) => setMessages(type, msgs),
    clearMessages: () => clearMessages(type),
    loadMessagesFromBackend: (userId) => loadMessagesFromBackend(userId, type),
  };
};

// Hook untuk akses clearAllMessages dari komponen lain
export const useChatContext = () => {
  const context = useContext(ChatContext);
  if (!context) {
    throw new Error("useChatContext must be used within ChatProvider");
  }
  return context;
};
