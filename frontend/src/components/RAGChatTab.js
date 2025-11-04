import React, { useState, useEffect, useRef } from "react";
import axios from "axios";
import { useChat } from "../contexts/chatcontext";
import { useUserId } from "../utils/userIdManager";
import MarkdownRenderer from './MarkdownRenderer';
import { Button } from './ui/button';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Send, FileText, Search, HelpCircle, BookOpen, MessageCircle, ArrowDown } from 'lucide-react';

const API_BASE = process.env.REACT_APP_API_URL;

// Helper untuk format waktu GMT+7
const formatTimestampGMT7 = (timestamp) => {
  const date = new Date(timestamp);
  return date.toLocaleTimeString('id-ID', {
    timeZone: 'Asia/Jakarta',
    hour: '2-digit',
    minute: '2-digit'
  });
};

function RAGChatTab() {
  const { messages, setMessages, clearMessages, loadMessagesFromBackend } = useChat('rag');
  const { userId, isAuthenticated, displayName, loading: userIdLoading } = useUserId();
  const [inputMessage, setInputMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [historyLoaded, setHistoryLoaded] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [showScrollButton, setShowScrollButton] = useState(false);
  const messagesEndRef = useRef(null);
  const chatContainerRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  // Handle scroll detection
  const handleScroll = (e) => {
    const container = e.target;
    const isNearBottom = container.scrollHeight - container.scrollTop - container.clientHeight < 100;
    setShowScrollButton(!isNearBottom);
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  // ⭐ Load chat history from backend when user is authenticated (NON-BLOCKING)
  useEffect(() => {
    const loadHistory = async () => {
      if (userId && isAuthenticated && !historyLoaded) {
        console.log('[RAGChatTab] Loading chat history from backend for user:', userId);
        setHistoryLoading(true);
        try {
          await loadMessagesFromBackend(userId, 'rag');
        } catch (error) {
          console.error('[RAGChatTab] Error loading history:', error);
        } finally {
          setHistoryLoaded(true);
          setHistoryLoading(false);
        }
      }
    };

    // Load history in background, don't block UI
    loadHistory();
  }, [userId, isAuthenticated, historyLoaded, loadMessagesFromBackend]);

  // Reset historyLoaded when user logs out
  useEffect(() => {
    if (!isAuthenticated) {
      setHistoryLoaded(false);
    }
  }, [isAuthenticated]);



  const sendMessage = async (message = inputMessage) => {
    if (!message.trim()) return;

    const userMessage = { role: "user", content: message, timestamp: new Date().toISOString() };
    setMessages([...messages, userMessage]);
    setInputMessage("");
    setLoading(true);

    try {
      const response = await axios.post(`${API_BASE}/rag-chat`, {
        message: message,
        user_id: userId  // Send actual user_id to backend (can be null for guest)
      }, {
        withCredentials: true
      });
      console.log("RAW ANSWER:", response.data.answer)

      const assistantMessage = {
        role: "assistant",
        content: response.data.answer,
        timestamp: new Date().toISOString()
      };
      setMessages([...messages, userMessage, assistantMessage]);
    } catch (error) {
      const errorMessage = {
        role: "assistant",
        content: `Error: ${error.response?.data?.detail || error.message}`,
        timestamp: new Date().toISOString(),
        error: true
      };
      setMessages([...messages, userMessage, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleQuickAction = async (action) => {
    const actionMessages = {
      'document list': 'Berapa dokumen yang tersedia dan apa saja?',
      'sop search': 'Tunjukkan semua SOP yang tersedia',
      'policy search': 'Apa saja kebijakan perusahaan yang ada?',
      'handbook search': 'Tampilkan informasi dari employee handbook',
      'procedure search': 'Cari prosedur kerja yang tersedia'
    };

    const message = actionMessages[action] || action;
    await sendMessage(message);
  };

  const containsTable = (content) => {
    return content.includes('|') && content.includes('---');
  };

  // Show minimal loading while fetching user ID (reduced delay)
  if (userIdLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading chat...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto px-4 py-6">
        <div className="grid gap-6 grid-cols-1 lg:grid-cols-3">
          {/* Quick Actions */}
          <div className="lg:col-span-1">
            <Card className="bg-card border-border">
              <CardHeader>
                <CardTitle>Quick Actions</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <Button
                  variant="outline"
                  onClick={() => handleQuickAction('document list')}
                  disabled={loading}
                  className="w-full justify-start"
                >
                  <FileText size={16} className="mr-2" />
                  <span>List All Documents</span>
                </Button>
                <Button
                  variant="outline"
                  onClick={() => handleQuickAction('sop search')}
                  disabled={loading}
                  className="w-full justify-start"
                >
                  <Search size={16} className="mr-2" />
                  <span>Search SOPs</span>
                </Button>
                <Button
                  variant="outline"
                  onClick={() => handleQuickAction('policy search')}
                  disabled={loading}
                  className="w-full justify-start"
                >
                  <HelpCircle size={16} className="mr-2" />
                  <span>Company Policies</span>
                </Button>
                <Button
                  variant="outline"
                  onClick={() => handleQuickAction('handbook search')}
                  disabled={loading}
                  className="w-full justify-start"
                >
                  <BookOpen size={16} className="mr-2" />
                  <span>Employee Handbook</span>
                </Button>
              </CardContent>
            </Card>
          </div>

          {/* Chat Area */}
          <div className="lg:col-span-2">
            <Card className="flex flex-col h-[80vh] bg-card border-border">
              <div className="flex items-center justify-between p-4 border-b border-border flex-shrink-0">
                <h3 className="text-xl font-semibold flex items-center">
                  <MessageCircle className="mr-2" size={20} />
                  Document Chat
                </h3>
              </div>

              <div className="flex flex-col flex-1 min-h-0 relative">
                <div
                  ref={chatContainerRef}
                  onScroll={handleScroll}
                  className="flex-1 overflow-y-auto p-4 space-y-4 min-h-0"
                >
                  {/* Loading history indicator - non-blocking */}
                  {historyLoading && messages.length === 0 && (
                    <div className="flex justify-center items-center py-4">
                      <div className="text-gray-500 text-sm flex items-center gap-2">
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                        <span>Loading conversation history...</span>
                      </div>
                    </div>
                  )}

                  {messages.map((msg, idx) => (
                    <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                      <div className={`px-4 py-2 rounded-lg ${
                        msg.role === 'user'
                          ? 'bg-blue-600 text-white max-w-xs lg:max-w-md'
                          : msg.error
                          ? 'bg-red-50 border border-red-200 text-red-800 max-w-xs lg:max-w-md'
                          : containsTable(msg.content)
                          ? 'bg-gray-100 dark:!bg-gray-700 text-gray-800 dark:!text-white w-full max-w-full'
                          : 'bg-gray-100 dark:!bg-gray-700 text-gray-800 dark:!text-white max-w-xs lg:max-w-md'
                      }`}>
                        {msg.role === 'assistant' ? (
                          <MarkdownRenderer content={msg.content} />
                        ) : (
                          <div className="whitespace-pre-wrap">{msg.content}</div>
                        )}
                        <div className={`text-xs mt-1 ${
                          msg.role === 'user' ? 'text-blue-100' : 'text-gray-500 dark:text-gray-400'
                        }`}>
                          {formatTimestampGMT7(msg.timestamp)}
                        </div>
                      </div>
                    </div>
                  ))}

                  {loading && (
                    <div className="flex justify-start">
                      <div className="bg-gray-100 dark:!bg-gray-700 rounded-lg px-4 py-2">
                        <div className="flex space-x-1">
                          <div className="w-2 h-2 bg-gray-400 dark:!bg-gray-500 rounded-full animate-bounce"></div>
                          <div className="w-2 h-2 bg-gray-400 dark:!bg-gray-500 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                          <div className="w-2 h-2 bg-gray-400 dark:!bg-gray-500 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                        </div>
                      </div>
                    </div>
                  )}
                  <div ref={messagesEndRef} />
                </div>

                {/* Scroll to Bottom Button */}
                {showScrollButton && (
                  <button
                    onClick={scrollToBottom}
                    className="absolute bottom-24 right-8 bg-blue-600 hover:bg-blue-700 text-white rounded-full p-3 shadow-lg transition-all duration-300 hover:scale-110 z-10"
                    aria-label="Scroll to bottom"
                  >
                    <ArrowDown size={20} />
                  </button>
                )}

                <div className="p-4 border-t border-border flex-shrink-0">
                  <div className="flex space-x-2">
                    <input
                      type="text"
                      value={inputMessage}
                      onChange={(e) => setInputMessage(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && !e.shiftKey && sendMessage()}
                      placeholder="Tanyakan tentang dokumen internal..."
                      disabled={loading}
                      className="flex-1 bg-background border border-input rounded-lg px-4 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring disabled:opacity-50"
                    />
                    <Button
                      onClick={() => sendMessage()}
                      disabled={loading || !inputMessage.trim()}
                      className="px-4"
                    >
                      <Send size={16} />
                    </Button>
                  </div>
                </div>
              </div>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}

export default RAGChatTab;