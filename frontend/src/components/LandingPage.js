import React, { useEffect, useState } from 'react';
import { Button } from './ui/button';
import ThemeToggle from './ThemeToggle';
import { Code } from 'lucide-react';

// Custom Toast Notification Component
const Toast = ({ message, title, type, onClose }) => {
  useEffect(() => {
    const timer = setTimeout(() => {
      onClose();
    }, 5000);
    return () => clearTimeout(timer);
  }, [onClose]);

  const bgColor = type === 'success' ? 'bg-green-600' : 'bg-red-600';
  const icon = type === 'success'
    ? <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
      </svg>
    : <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
      </svg>;

  return (
    <div style={{
      position: 'fixed',
      top: '20px',
      right: '20px',
      zIndex: 9999,
      minWidth: '320px',
      maxWidth: '400px',
      backgroundColor: '#1f2937',
      border: '1px solid #374151',
      borderRadius: '8px',
      boxShadow: '0 10px 25px rgba(0, 0, 0, 0.3)',
      overflow: 'hidden',
      animation: 'slideIn 0.3s ease-out'
    }}>
      <div className={`${bgColor} px-4 py-3 flex items-center justify-between`}>
        <div className="flex items-center gap-3 text-white">
          {icon}
          <span className="font-semibold text-sm">{title}</span>
        </div>
        <button
          onClick={onClose}
          className="text-white hover:bg-white/20 rounded p-1 transition-colors"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
      <div className="px-4 py-3 text-gray-200 text-sm leading-relaxed">
        {message}
      </div>
    </div>
  );
};

const LandingPage = ({ onGetStarted }) => {
  const [toast, setToast] = useState(null);

  const handleMicrosoftLogin = () => {
    window.location.href = `${process.env.REACT_APP_API_URL}/auth/microsoft`;
  };

  useEffect(() => {
    // Listen for postMessage from popup
    const handleMessage = (event) => {
      // Verify origin
      if (event.origin !== process.env.REACT_APP_API_URL) return;

      const { type, title, message } = event.data;

      if (type === 'auth_success') {
        // Show success toast
        setToast({
          type: 'success',
          title: title || 'Success',
          message: message || 'Authentication successful'
        });

        // Set authenticated
        localStorage.setItem('isAuthenticated', 'true');

        // Call success callback after short delay
        setTimeout(() => {
          if (onGetStarted) {
            onGetStarted();
          }
        }, 1500);
      } else if (type === 'auth_error') {
        // Show error toast
        setToast({
          type: 'error',
          title: title || 'Error',
          message: message || 'Authentication failed'
        });
      }
    };

    window.addEventListener('message', handleMessage);

    // Also check URL params for fallback
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('authenticated') === 'true') {
      localStorage.setItem('isAuthenticated', 'true');
      if (onGetStarted) {
        onGetStarted();
      }
      window.history.replaceState({}, document.title, window.location.pathname);
    }

    return () => {
      window.removeEventListener('message', handleMessage);
    };
  }, [onGetStarted]);

  return (
    <>
      {toast && (
        <Toast
          type={toast.type}
          title={toast.title}
          message={toast.message}
          onClose={() => setToast(null)}
        />
      )}

    <div className="min-h-screen bg-background text-foreground">
      {/* Navigation */}
      <nav className="border-b border-border">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            {/* Logo */}
            <div className="flex items-center gap-2">
              <img src="/logo_proficient.png" alt="Pro-Ficient" className="h-16 w-16" />
              <span className="font-medium">Pro-Ficient</span>
            </div>

            {/* Theme Toggle */}
            <ThemeToggle variant="switch" />
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="min-h-screen flex flex-col justify-center text-center px-4">
          <h1 className="text-4xl md:text-6xl font-semibold bg-gradient-to-r from-[#1a1a26] to-[#d3d3d3] bg-clip-text text-transparent tracking-tight">
            PRO-FICIENT 
          </h1>
          <div className="max-w-4xl mx-auto space-y-4 mb-12">
            <p className="text-2xl md:text-4xl text-muted-foreground leading-relaxed">
              Seamless Intelligence for Limitless Productivity
            </p>
          </div>

          {/* CTA Buttons */}
          <div className="flex justify-center gap-4">
            <Button onClick={handleMicrosoftLogin} size="lg">
              Try Now
            </Button>
            <Button
              variant="outline"
              size="lg"
              onClick={() => {
                document.getElementById('features')?.scrollIntoView({
                  behavior: 'smooth',
                  block: 'start'
                });
              }}
            >
              Learn More
            </Button>
          </div>
        </div>

          {/* Features Section */}
          <div id="features" className="min-h-screen flex flex-col justify-center py-20">
            <h2 className="text-3xl font-bold mb-4">
              Powerful AI Tools
            </h2>
            <p className="text-muted-foreground mb-12">
              Access a suite of AI-powered tools designed to streamline your development process
            </p>

            {/* Feature Cards */}
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-6xl mx-auto">
              {/* AI Code Assistant */}
              <div className="bg-card border border-border rounded-xl p-6 text-left hover:shadow-lg transition-shadow">
                <div className="mb-4">
                  <Code className="h-6 w-6 text-foreground" />
                </div>
                <h3 className="text-lg font-semibold mb-2">
                  AI Document Assistant
                </h3>
                <p className="text-muted-foreground text-sm">
                  Get instant answers from internal company documents such as SOPs, guidelines, and HR policies, providing accurate and context-based information in real time.
                </p>
              </div>

              {/* Bug Finder & Fixer */}
              <div className="bg-card border border-border rounded-xl p-6 text-left hover:shadow-lg transition-shadow">
                <div className="w-12 h-12 bg-muted rounded-lg flex items-center justify-center mb-4">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" className="text-foreground">
                    <path d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                </div>
                <h3 className="text-lg font-semibold mb-2">
                  Project Management
                </h3>
                <p className="text-muted-foreground text-sm">
                  Monitor ongoing projects, view team progress, and check deadlines directly from Microsoft Planner.
                </p>
              </div>

              {/* Documentation Generator */}
              <div className="bg-card border border-border rounded-xl p-6 text-left hover:shadow-lg transition-shadow">
                <div className="w-12 h-12 bg-muted rounded-lg flex items-center justify-center mb-4">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" className="text-foreground">
                    <path d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                </div>
                <h3 className="text-lg font-semibold mb-2">
                    Smart To-do
                </h3>
                <p className="text-muted-foreground text-sm">
                  Stay organized by efficiently managing tasks, deadlines, and meetings through integration with Microsoft To-Do.
                </p>
              </div>

            </div>
          </div>
      </main>
    </div>

    <style jsx>{`
      @keyframes slideIn {
        from {
          transform: translateX(100%);
          opacity: 0;
        }
        to {
          transform: translateX(0);
          opacity: 1;
        }
      }
    `}</style>
    </>
  );
};

export default LandingPage;
