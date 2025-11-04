import React, { useState, useEffect, useRef } from 'react';
import { Send, List, BarChart3, AlertTriangle, Target, Calendar, MessageCircle, ArrowDown } from 'lucide-react';
import { useChat } from '../contexts/chatcontext';
import { useUserId } from '../utils/userIdManager';
import MarkdownRenderer from './MarkdownRenderer';
import { Button } from './ui/button';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';


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





function SmartProjectApp() {
  const { messages: chatMessages, setMessages: setChatMessages, loadMessagesFromBackend } = useChat('project');
  const { userId, isAuthenticated } = useUserId();
  const [currentMessage, setCurrentMessage] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const chatContainerRef = useRef(null);
  const [showScrollButton, setShowScrollButton] = useState(false);
  const [historyLoaded, setHistoryLoaded] = useState(false);

  // Load chat history from backend when user is authenticated
  useEffect(() => {
    const loadHistory = async () => {
      if (userId && isAuthenticated && !historyLoaded) {
        console.log('[SmartProjectApp] Loading chat history from backend for user:', userId);
        await loadMessagesFromBackend(userId);
        setHistoryLoaded(true);
      }
    };

    loadHistory();
  }, [userId, isAuthenticated, historyLoaded, loadMessagesFromBackend]);

  // Reset historyLoaded when user logs out
  useEffect(() => {
    if (!isAuthenticated) {
      setHistoryLoaded(false);
    }
  }, [isAuthenticated]);



  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatMessages, chatLoading]);

  const handleScroll = (e) => {
    const container = e.target;
    const isNearBottom = container.scrollHeight - container.scrollTop - container.clientHeight < 100;
    setShowScrollButton(!isNearBottom);
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };





  const sendChatMessage = async (message = currentMessage) => {
    if (!message.trim()) return;

    // Debug: Check userId before sending
    console.log('[SmartProjectApp] Sending message with userId:', userId);
    console.log('[SmartProjectApp] isAuthenticated:', isAuthenticated);

    if (!userId) {
      console.error('[SmartProjectApp] ❌ userId is null/undefined, cannot send request');
      const errorMessage = {
        role: 'assistant',
        content: '❌ User ID not found. Please refresh the page and login again.',
        timestamp: new Date().toISOString(),
        error: true
      };
      setChatMessages([...chatMessages, errorMessage]);
      return;
    }

    const userMessage = {
      role: 'user',
      content: message,
      timestamp: new Date().toISOString()
    };

    setChatMessages([...chatMessages, userMessage]);
    setCurrentMessage('');
    setChatLoading(true);

    try {
      console.log('[SmartProjectApp] Sending fetch request to:', `${API_BASE}/project-chat`);
      const response = await fetch(`${API_BASE}/project-chat`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message,
          user_id: userId
        })
      });
      console.log('[SmartProjectApp] Response status:', response.status);

      const data = await response.json();
      
      if (data.job_id) {
        pollJobStatus(data.job_id);
      } else {
        const assistantMessage = {
          role: 'assistant',
          content: data.answer || 'No response received',
          timestamp: new Date().toISOString()
        };
        setChatMessages([...chatMessages, userMessage, assistantMessage]);
        setChatLoading(false);
      }
    } catch (error) {
      console.error('Chat error:', error);
      const errorMessage = {
        role: 'assistant',
        content: 'Error processing your request. Please try again.',
        timestamp: new Date().toISOString(),
        error: true
      };
      setChatMessages([...chatMessages, userMessage, errorMessage]);
      setChatLoading(false);
    }
  };

  const pollJobStatus = async (jobId) => {
    const interval = setInterval(async () => {
      try {
        const response = await fetch(`${API_BASE}/job-status/${jobId}`);
        const status = await response.json();
        
        if (status.status === 'completed') {
          clearInterval(interval);
          setChatLoading(false);
          
          const assistantMessage = {
            role: 'assistant',
            content: status.result,
            timestamp: new Date().toISOString()
          };

          setChatMessages(prev => [...prev, assistantMessage]);

        } else if (status.status === 'failed') {
          clearInterval(interval);
          setChatLoading(false);

          const errorMessage = {
            role: 'assistant',
            content: `Error: ${status.error || 'Processing failed'}`,
            timestamp: new Date().toISOString(),
            error: true
          };

          setChatMessages(prev => [...prev, errorMessage]);
        }
      } catch (error) {
        console.error('Polling error:', error);
        clearInterval(interval);
        setChatLoading(false);
      }
    }, 2000);
  };

  const handleQuickAction = async (action) => {
    const actionMessages = {
      'list project': 'Tampilkan semua project dengan status dan progress lengkap',
      'portfolio overview': 'Berikan overview progress semua project dengan insight dan recommendations',
      'problem analysis': 'Identifikasi project yang bermasalah atau tertinggal dengan analisis root cause',
      'priority ranking': 'Ranking project berdasarkan prioritas dan urgency dengan actionable recommendations',
      'weekly summary': 'Buatkan weekly summary semua project dengan achievement dan next steps'
    };

    const message = actionMessages[action] || action;
    await sendChatMessage(message);
  };

  const containsTable = (content) => {
    return content.includes('|') && content.includes('---');
  };

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto px-4 py-6">
        <div className="grid gap-6 grid-cols-1 lg:grid-cols-3">
          {/* Quick Actions */}
          <div className="lg:col-span-1">
            <Card className="mb-6 bg-card border-border">
              <CardHeader>
                <CardTitle>Quick Actions</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <Button
                  variant="outline"
                  onClick={() => handleQuickAction('list project')}
                  disabled={chatLoading}
                  className="w-full justify-start"
                >
                  <List size={16} className="mr-2" />
                  <span>List All Projects</span>
                </Button>
                <Button
                  variant="outline"
                  onClick={() => handleQuickAction('portfolio overview')}
                  disabled={chatLoading}
                  className="w-full justify-start"
                >
                  <BarChart3 size={16} className="mr-2" />
                  <span>Portfolio Overview</span>
                </Button>
                <Button
                  variant="outline"
                  onClick={() => handleQuickAction('problem analysis')}
                  disabled={chatLoading}
                  className="w-full justify-start"
                >
                  <AlertTriangle size={16} className="mr-2" />
                  <span>Problem Analysis</span>
                </Button>
                <Button
                  variant="outline"
                  onClick={() => handleQuickAction('priority ranking')}
                  disabled={chatLoading}
                  className="w-full justify-start"
                >
                  <Target size={16} className="mr-2" />
                  <span>Priority Ranking</span>
                </Button>
                <Button
                  variant="outline"
                  onClick={() => handleQuickAction('weekly summary')}
                  disabled={chatLoading}
                  className="w-full justify-start"
                >
                  <Calendar size={16} className="mr-2" />
                  <span>Weekly Summary</span>
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
                  Smart Project Chat
                </h3>
              </div>

              <div className="flex flex-col flex-1 min-h-0 relative">
                <div ref={chatContainerRef} onScroll={handleScroll} className="flex-1 overflow-y-auto p-4 space-y-4 min-h-0">
                  {chatMessages.map((msg, idx) => (
                    <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                      <div className={`px-4 py-2 rounded-lg ${
                        msg.role === 'user' 
                          ? 'bg-blue-600 text-white max-w-xs lg:max-w-md' 
                          : msg.error 
                          ? 'bg-red-50 border border-red-200 text-red-800 max-w-xs lg:max-w-md'
                          : containsTable(msg.content)
                          ? 'bg-gray-100 dark:!bg-gray-700 text-gray-800 dark:!text-gray-200 w-full max-w-full'
                          : 'bg-gray-100 dark:!bg-gray-700 text-gray-800 dark:!text-gray-200 max-w-xs lg:max-w-md'
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
                  
                  {chatLoading && (
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
                      value={currentMessage}
                      onChange={(e) => setCurrentMessage(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && !e.shiftKey && sendChatMessage()}
                      placeholder="Ask about your projects..."
                      disabled={chatLoading}
                      className="flex-1 bg-background border border-input rounded-lg px-4 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring disabled:opacity-50"
                    />
                    <Button
                      onClick={() => sendChatMessage()}
                      disabled={chatLoading || !currentMessage.trim()}
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

export default SmartProjectApp;