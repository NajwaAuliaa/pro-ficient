import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import UploadTab from './components/UploadTab';
import RAGChatTab from './components/RAGChatTab';
import SmartProjectApp from './components/SmartProjectManagement';
import TodoTab from './components/TodoTab';
import LandingPage from './components/LandingPage';
import ThemeToggle from './components/ThemeToggle';
import { ChatProvider, useChatContext } from './contexts/chatcontext';
import { ThemeProvider, useTheme } from './contexts/ThemeContext';
import './App.css';

function AppContent() {
  const [activeTab, setActiveTab] = useState('rag');
  const [currentView, setCurrentView] = useState('landing'); // 'landing', 'app'
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true); // Start with loading=true to check auth first

  // Get clearAllMessages function from ChatContext
  const { clearAllMessages } = useChatContext();

  // Get theme state
  const { isDark } = useTheme();

  const handleLoginSuccess = () => {
    setIsAuthenticated(true);
    setCurrentView('app');
  };

  const handleLogout = async () => {
    try {
      console.log('[Logout] Starting logout process...');

      // Get session_id before clearing
      const sessionId = sessionStorage.getItem('user_session_id');

      // Call backend logout endpoint with session_id
      await fetch(`${process.env.REACT_APP_API_URL}/auth/logout`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ session_id: sessionId }),
        credentials: 'include' // Still send cookies for backward compatibility
      });

      console.log('[Logout] ✅ Backend logout successful');

      // ⭐ IMPORTANT: Clear frontend state, but backend memory (Cosmos DB) persists
      clearAllMessages(); // Only clears React state, not backend
      console.log('[Logout] ✅ Chat messages cleared from React state (backend preserved)');

      // 🔧 PERBAIKAN: Clear only auth-related data, preserve theme
      localStorage.removeItem('isAuthenticated');
      localStorage.removeItem('user');
      localStorage.removeItem('token');
      sessionStorage.removeItem('user_session_id'); // Clear session_id
      sessionStorage.clear();

      console.log('[Logout] ✅ Auth data cleared (theme preserved)');

      // Force state reset - IMPORTANT: Do this before reload
      setIsAuthenticated(false);
      setCurrentView('landing');

      console.log('[Logout] ✅ Redirecting to landing page...');

      // Force page reload to completely reset application state
      // This ensures no stale React state remains
      setTimeout(() => {
        window.location.href = '/';
      }, 100);

    } catch (error) {
      console.error('[Logout] ❌ Logout error:', error);

      // Force logout even if API call fails
      clearAllMessages();

      // Clear only auth-related data, preserve theme
      localStorage.removeItem('isAuthenticated');
      localStorage.removeItem('user');
      localStorage.removeItem('token');
      sessionStorage.removeItem('user_session_id'); // Clear session_id
      sessionStorage.clear();

      setIsAuthenticated(false);
      setCurrentView('landing');

      setTimeout(() => {
        window.location.href = '/';
      }, 100);
    }
  };

  // Check authentication on mount
  useEffect(() => {
    const checkAuth = async () => {
      try {
        // 🔧 NEW: Check if session_id in URL (from OAuth redirect)
        const urlParams = new URLSearchParams(window.location.search);
        const sessionIdFromUrl = urlParams.get('session_id');

        if (sessionIdFromUrl) {
          console.log('[Auth] Got session_id from URL:', sessionIdFromUrl);
          sessionStorage.setItem('user_session_id', sessionIdFromUrl);
          // Clean URL without reload
          window.history.replaceState({}, '', window.location.pathname);
        }

        // Get session_id from sessionStorage
        const sessionId = sessionStorage.getItem('user_session_id');

        // Use the unified /auth/me endpoint with session_id in body
        const response = await fetch(`${process.env.REACT_APP_API_URL}/auth/me`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ session_id: sessionId }),
          credentials: 'include' // Important: send cookies for backward compatibility
        });

        const data = await response.json();

        // Check if user is authenticated and has valid user_id
        const authenticated = data.authenticated && data.user_id;

        console.log('[Auth Check]', {
          authenticated,
          user_id: data.user_id,
          email: data.email
        });

        setIsAuthenticated(authenticated);

        if (authenticated) {
          // User is authenticated, show app
          setCurrentView('app');
          console.log('[Auth Check] ✅ User authenticated, showing app');
        } else {
          // User is NOT authenticated, must go to landing page
          console.log('[Auth Check] ❌ User not authenticated, redirecting to landing');

          // Clear frontend state only (backend memory persists in Cosmos DB)
          clearAllMessages();

          // Clear only auth-related data, preserve theme
          localStorage.removeItem('isAuthenticated');
          localStorage.removeItem('user');
          localStorage.removeItem('token');
          sessionStorage.removeItem('user_session_id'); // Clear session_id
          sessionStorage.clear();

          // IMPORTANT: Force to landing page, NOT app
          setCurrentView('landing');
          setIsAuthenticated(false);

          console.log('[Auth Check] ✅ Frontend cleared, user must login to access backend memory');
        }
      } catch (error) {
        console.error('[Auth Check Error]', error);

        // On error, treat as not authenticated
        setIsAuthenticated(false);
        setCurrentView('landing');

        // Clear stale frontend data
        clearAllMessages();

        // Clear only auth-related data, preserve theme
        localStorage.removeItem('isAuthenticated');
        localStorage.removeItem('user');
        localStorage.removeItem('token');
        sessionStorage.removeItem('user_session_id'); // Clear session_id
        sessionStorage.clear();
      } finally {
        setLoading(false);
      }
    };

    checkAuth();
  }, [clearAllMessages]);

  if (loading) {
    return <div className="flex items-center justify-center h-screen">Loading...</div>;
  }

  // Show landing page
  if (currentView === 'landing') {
    return <LandingPage onGetStarted={handleLoginSuccess} />;
  }

  // Show main app
  if (currentView === 'app' && isAuthenticated) {
    return (
      <div className="flex h-screen bg-background">
        <Sidebar active={activeTab} onChange={setActiveTab} />
        <main className="flex-1 flex flex-col overflow-hidden">
          <header className="border-b border-border bg-card px-6 py-4 flex items-center justify-between shadow-sm">
            <div className="flex items-center gap-3">
              <img src={isDark ? "/SoftwareOneDarkmode.png" : "/softwareone.png"} alt="SoftwareOne" className="h-8" />
              <div className="h-8 w-px bg-border"></div>
              <h1 className="text-xl font-semibold text-foreground mt-7">
                Pro-Ficient
              </h1>
            </div>
            <div className="flex items-center gap-3">
              <ThemeToggle />
              <button
                onClick={handleLogout}
                className="px-4 py-2 text-sm font-medium text-foreground bg-card border border-border rounded-md hover:bg-accent focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-ring transition-colors"
              >
                Logout
              </button>
            </div>
          </header>

          <div className="flex-1 overflow-auto">
            {activeTab === 'upload' && <UploadTab />}

            {activeTab === 'rag' && (
              <ChatProvider type="rag">
                <RAGChatTab />
              </ChatProvider>
            )}

            {activeTab === 'todo' && (
              <ChatProvider type="todo">
                <TodoTab />
              </ChatProvider>
            )}

            {activeTab === 'project' && (
              <ChatProvider type="project">
                <SmartProjectApp />
              </ChatProvider>
            )}
          </div>
        </main>
      </div>
    );
  }

  // Fallback (should not reach here normally)
  return null;
}

// Wrap with ThemeProvider
function App() {
  return (
    <ThemeProvider>
      <AppContent />
    </ThemeProvider>
  );
}

export default App;