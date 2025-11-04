import React from 'react';
import { Moon, Sun } from 'lucide-react';
import { useTheme } from '../contexts/ThemeContext';

const ThemeToggle = ({ variant = 'default' }) => {
  const { theme, toggleTheme, isDark } = useTheme();

  if (variant === 'switch') {
    return (
      <div className="flex items-center gap-3">
        <Sun className={`w-4 h-4 transition-colors ${
          isDark ? 'text-muted-foreground' : 'text-amber-500'
        }`} />

        <button
          onClick={toggleTheme}
          className={`relative w-14 h-7 rounded-full transition-all duration-300 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary ${
            isDark 
              ? 'bg-gradient-to-r from-blue-600 to-blue-700 shadow-lg' 
              : 'bg-gradient-to-r from-gray-200 to-gray-300 shadow-inner'
          }`}
          aria-label="Toggle theme"
        >
          <div
            className={`absolute top-0.5 w-6 h-6 bg-white rounded-full shadow-md transition-all duration-300 flex items-center justify-center ${
              isDark ? 'translate-x-7' : 'translate-x-0.5'
            }`}
          >
            {isDark ? (
              <Moon className="w-3 h-3 text-blue-600" />
            ) : (
              <Sun className="w-3 h-3 text-amber-500" />
            )}
          </div>
        </button>

        <Moon className={`w-4 h-4 transition-colors ${
          isDark ? 'text-blue-400' : 'text-muted-foreground'
        }`} />
      </div>
    );
  }

  // Default: Simple icon toggle
  return (
    <button
      onClick={toggleTheme}
      className="w-10 h-10 rounded-lg flex items-center justify-center hover:bg-accent transition-colors"
      aria-label={`Switch to ${isDark ? 'light' : 'dark'} mode`}
    >
      {isDark ? (
        <Sun className="w-5 h-5 text-foreground" />
      ) : (
        <Moon className="w-5 h-5 text-foreground" />
      )}
    </button>
  );
};

export default ThemeToggle;
