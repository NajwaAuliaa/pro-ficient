import React, { useState } from 'react';
import {
  Upload,
  MessageSquare,
  ListChecks,
  ClipboardList,
  Menu,
  X,
  ChevronDown,
  ChevronRight,
  Bot,
  Code,
  Bug,
  BookOpen,
  Regex,
  FlaskConical,
  GitCommit
} from 'lucide-react';

function Sidebar({ active, onChange }) {
  const [isOpen, setIsOpen] = useState(true);
  const [isInternalAssistantOpen, setIsInternalAssistantOpen] = useState(true);

  // Menu items dengan style baru
  const internalAssistantItems = [
    {
      id: 'upload',
      icon: Upload,
      title: 'Upload Document',
      description: 'Upload and manage your documents'
    },
    {
      id: 'rag',
      icon: Code,
      title: 'AI Document Assistant',
      description: 'Get intelligent document suggestions and completions'
    },
    {
      id: 'project',
      icon: ClipboardList,
      title: 'Project Management',
      description: 'Manage your projects efficiently'
    },
    {
      id: 'todo',
      icon: ListChecks,
      title: 'Smart To-Do',
      description: 'AI-powered task management'
    }
  ];


  return (
    <div
      className={`${
        isOpen ? 'w-80' : 'w-16'
      } h-screen flex flex-col transition-all duration-300 bg-background border-r border-border`}
    >
      {/* Header */}
      <div className="p-4 border-b border-border">
        <div className="flex items-center justify-end">
          <button
            className="flex-shrink-0 w-10 h-10 rounded-lg flex items-center justify-center hover:bg-accent transition-colors"
            onClick={() => setIsOpen(!isOpen)}
          >
            {isOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>
      </div>

      {/* Menu Items */}
      <div className="flex-1 overflow-y-auto p-3 space-y-2">
        {/* Internal Assistant Section Header */}
        <button
          className={`
            w-full rounded-lg text-left transition-all
            ${isOpen ? 'p-3' : 'p-2 justify-center'}
            hover:bg-accent
          `}
          onClick={() => setIsInternalAssistantOpen(!isInternalAssistantOpen)}
        >
          {isOpen ? (
            <div className="flex items-center gap-3">
              <div className="w-5 h-5 flex items-center justify-center">
                {isInternalAssistantOpen ? (
                  <ChevronDown size={16} />
                ) : (
                  <ChevronRight size={16} />
                )}
              </div>
              <div className="p-2 bg-muted rounded-lg">
                <Bot size={18} />
              </div>
              <span className="font-medium text-sm">Internal Assistant</span>
            </div>
          ) : (
            <div className="flex justify-center">
              <Bot size={20} />
            </div>
          )}
        </button>

        {/* Internal Assistant Sub-menu */}
        {isInternalAssistantOpen && isOpen && (
          <div className="space-y-1.5 ml-2">
            {internalAssistantItems.map((item) => {
              const Icon = item.icon;
              const isActive = active === item.id;

              return (
                <button
                  key={item.id}
                  onClick={() => onChange(item.id)}
                  className={`
                    w-full p-3 rounded-lg text-left transition-all
                    ${
                      isActive
                        ? 'bg-primary text-primary-foreground shadow-md'
                        : 'bg-card hover:bg-accent text-card-foreground hover:text-accent-foreground'
                    }
                  `}
                >
                  <div className="flex items-start gap-3">
                    <div
                      className={`
                      p-2 rounded-lg flex-shrink-0
                      ${isActive ? 'bg-primary-foreground/20' : 'bg-muted'}
                    `}
                    >
                      <Icon className="w-4 h-4" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <h3 className="font-semibold text-sm mb-0.5 truncate">
                        {item.title}
                      </h3>
                      <p
                        className={`
                        text-xs line-clamp-2
                        ${
                          isActive
                            ? 'text-primary-foreground/80'
                            : 'text-muted-foreground'
                        }
                      `}
                      >
                        {item.description}
                      </p>
                    </div>
                  </div>
                </button>
              );
            })}
          </div>
        )}

        {/* Collapsed Internal Assistant Sub-menu */}
        {isInternalAssistantOpen && !isOpen && (
          <div className="space-y-1">
            {internalAssistantItems.map((item) => {
              const Icon = item.icon;
              const isActive = active === item.id;

              return (
                <button
                  key={item.id}
                  onClick={() => onChange(item.id)}
                  className={`
                    w-full p-2 rounded-lg flex justify-center transition-all
                    ${
                      isActive
                        ? 'bg-primary text-primary-foreground'
                        : 'hover:bg-accent'
                    }
                  `}
                  title={item.title}
                >
                  <Icon size={18} />
                </button>
              );
            })}
          </div>
        )}

      </div>
    </div>
  );
}

export default Sidebar;
