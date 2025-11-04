import React, { useState, useEffect, useRef } from 'react';
import { Send, CheckSquare, Clock, AlertCircle, Plus, Calendar, MessageCircle, ArrowDown } from 'lucide-react';
import { useChat } from '../contexts/chatcontext';
import { useUserId } from '../utils/userIdManager';
import MarkdownRenderer from './MarkdownRenderer';
import { Button } from './ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from './ui/card';
import axios from 'axios';

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





function TodoTab() {
  const { messages: chatMessages, setMessages: setChatMessages, loadMessagesFromBackend } = useChat('todo');
  const { userId, isAuthenticated, displayName, loading: userIdLoading } = useUserId();
  const [currentMessage, setCurrentMessage] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [taskForm, setTaskForm] = useState({ name: '', deadline: '', description: '' });
  const [showScrollButton, setShowScrollButton] = useState(false);
  const messagesEndRef = useRef(null);
  const chatContainerRef = useRef(null);

  const [historyLoaded, setHistoryLoaded] = useState(false);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatMessages, chatLoading]);

  // Handle scroll detection
  const handleScroll = (e) => {
    const container = e.target;
    const isNearBottom = container.scrollHeight - container.scrollTop - container.clientHeight < 100;
    setShowScrollButton(!isNearBottom);
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  // ⭐ Load chat history from backend when user is authenticated
  useEffect(() => {
    const loadHistory = async () => {
      if (userId && isAuthenticated && !historyLoaded) {
        console.log('[TodoTab] Loading chat history from backend for user:', userId);
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

  const sendChatMessage = async (message = currentMessage) => {
    if (!message.trim()) return;

    // Debug: Check userId before sending
    console.log('[TodoTab] Sending message with userId:', userId);
    console.log('[TodoTab] isAuthenticated:', isAuthenticated);

    if (!userId) {
      console.error('[TodoTab] ❌ userId is null/undefined, cannot send request');
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
      console.log('[TodoTab] Sending fetch request to:', `${API_BASE}/todo-chat`);
      const response = await fetch(`${API_BASE}/todo-chat`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message,
          user_id: userId  // Send user_id from cookie-based auth
        })
      });
      console.log('[TodoTab] Response status:', response.status);

      const data = await response.json();
      
      const assistantMessage = {
        role: 'assistant',
        content: data.answer || 'No response received',
        timestamp: new Date().toISOString()
      };
      setChatMessages([...chatMessages, userMessage, assistantMessage]);
    } catch (error) {
      console.error('Chat error:', error);
      const errorMessage = {
        role: 'assistant',
        content: 'Error processing your request. Please try again.',
        timestamp: new Date().toISOString(),
        error: true
      };
      setChatMessages([...chatMessages, userMessage, errorMessage]);
    } finally {
      setChatLoading(false);
    }
  };

  const handleQuickAction = async (action) => {
    const actionMessages = {
      'list tasks': 'Tampilkan semua task saya dengan status dan deadline',
      'today tasks': 'Task apa saja yang deadline hari ini?',
      'overdue tasks': 'Tunjukkan task yang sudah overdue dengan prioritas',
      'productivity': 'Analisis produktivitas saya minggu ini dan berikan insight'
    };

    const message = actionMessages[action] || action;
    await sendChatMessage(message);
  };

  const handleCreateTask = () => {
    const message = `Buat task baru, nama task: ${taskForm.name}, deadline: ${taskForm.deadline}, deskripsi: ${taskForm.description}`;
    sendChatMessage(message);
    setShowCreateForm(false);
    setTaskForm({ name: '', deadline: '', description: '' });
  };

  const containsTable = (content) => {
    return content.includes('|') && content.includes('---');
  };

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto px-4 py-6">
        <div className="grid gap-6 grid-cols-1 lg:grid-cols-3">
          {/* Quick Actions */}
          <div className="lg:col-span-1 space-y-4">
            <Card className="mb-6 bg-card border-border">
              <CardHeader>
                <CardTitle>Quick Actions</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <Button
                  variant="outline"
                  onClick={() => handleQuickAction('list tasks')}
                  disabled={chatLoading}
                  className="w-full justify-start"
                >
                  <CheckSquare size={16} className="mr-2" />
                  <span>List All Tasks</span>
                </Button>
                <Button
                  variant="outline"
                  onClick={() => handleQuickAction('today tasks')}
                  disabled={chatLoading}
                  className="w-full justify-start"
                >
                  <Calendar size={16} className="mr-2" />
                  <span>Today's Tasks</span>
                </Button>
                <Button
                  variant="outline"
                  onClick={() => handleQuickAction('overdue tasks')}
                  disabled={chatLoading}
                  className="w-full justify-start"
                >
                  <AlertCircle size={16} className="mr-2" />
                  <span>Overdue Tasks</span>
                </Button>
                <Button
                  variant="outline"
                  onClick={() => setShowCreateForm(true)}
                  disabled={chatLoading}
                  className="w-full justify-start"
                >
                  <Plus size={16} className="mr-2" />
                  <span>Create New Task</span>
                </Button>
                <Button
                  variant="outline"
                  onClick={() => handleQuickAction('productivity')}
                  disabled={chatLoading}
                  className="w-full justify-start"
                >
                  <Clock size={16} className="mr-2" />
                  <span>Productivity Analysis</span>
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
                  Smart To-Do Assistant
                </h3>
              </div>

              <div className="flex flex-col flex-1 min-h-0 relative">
                <div
                  ref={chatContainerRef}
                  onScroll={handleScroll}
                  className="flex-1 overflow-y-auto p-4 space-y-4 min-h-0"
                >
                  {chatMessages.map((msg, idx) => (
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
                      value={currentMessage}
                      onChange={(e) => setCurrentMessage(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && !e.shiftKey && sendChatMessage()}
                      placeholder="Tanyakan tentang task atau buat task baru..."
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

        {/* Create Task Form Modal */}
        {showCreateForm && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
            <Card className="max-w-md w-full bg-card border-border">
              <CardHeader>
                <CardTitle>Create New Task</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-1 text-foreground">Task Name</label>
                  <input
                    type="text"
                    value={taskForm.name}
                    onChange={(e) => setTaskForm({...taskForm, name: e.target.value})}
                    className="w-full bg-background border border-input rounded-lg px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                    placeholder="Enter task name"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1 text-foreground">Deadline</label>
                  <input
                    type="date"
                    value={taskForm.deadline}
                    onChange={(e) => setTaskForm({...taskForm, deadline: e.target.value})}
                    className="w-full bg-background border border-input rounded-lg px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1 text-foreground">Description</label>
                  <textarea
                    value={taskForm.description}
                    onChange={(e) => setTaskForm({...taskForm, description: e.target.value})}
                    className="w-full bg-background border border-input rounded-lg px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                    rows="3"
                    placeholder="Enter task description"
                  />
                </div>
              </CardContent>
              <div className="flex space-x-2 px-6 pb-6">
                <Button
                  variant="outline"
                  onClick={() => setShowCreateForm(false)}
                  className="flex-1"
                >
                  Cancel
                </Button>
                <Button
                  onClick={handleCreateTask}
                  disabled={!taskForm.name.trim()}
                  className="flex-1"
                >
                  Create Task
                </Button>
              </div>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
}

export default TodoTab;