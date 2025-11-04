import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';

const MarkdownRenderer = ({ content }) => {
  // Process content to handle HTML entities and tags
  const processContent = (text) => {
    if (!text) return '';
    
    return text
      // Convert HTML entities to actual HTML
      .replace(/&lt;br&gt;/gi, '<br>')
      .replace(/&lt;br\/&gt;/gi, '<br>')
      .replace(/&lt;br \/&gt;/gi, '<br>')
      .replace(/&amp;lt;br&amp;gt;/gi, '<br>')
      .replace(/&nbsp;/gi, ' ')
      .replace(/&amp;/gi, '&')
      .replace(/&lt;/gi, '<')
      .replace(/&gt;/gi, '>')
      // Ensure proper line breaks around tables
      .replace(/(\|[^\n]+\|)\n*(\|[^\n]+\|)/g, '$1\n$2');
  };

  return (
    <div className="markdown-content prose prose-sm max-w-none">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeRaw]}
        components={{
          // Table components
          table: ({ node, ...props }) => (
            <div className="overflow-x-auto my-6 shadow-lg rounded-lg">
              <table
                className="w-full border-collapse bg-white dark:bg-gray-800 text-sm"
                {...props}
              />
            </div>
          ),

          thead: ({ node, ...props }) => (
            <thead className="bg-blue-600 dark:bg-blue-800" {...props} />
          ),

          tbody: ({ node, ...props }) => (
            <tbody className="divide-y divide-gray-200 dark:divide-gray-700 [&>tr:hover]:bg-gray-50 dark:[&>tr:hover]:bg-gray-700/50" {...props} />
          ),

          tr: ({ node, ...props }) => (
            <tr className="transition-colors" {...props} />
          ),

          th: ({ node, ...props }) => (
            <th
              className="px-4 py-3 text-left font-bold text-white border border-gray-300 dark:border-gray-600 text-sm"
              {...props}
            />
          ),

          td: ({ node, ...props }) => (
            <td
              className="px-4 py-3 border border-gray-300 dark:border-gray-600 align-top text-gray-800 dark:text-white"
              {...props}
            />
          ),
          
          // Text components
          h1: ({ node, ...props }) => (
            <h1 className="text-2xl font-bold mb-4 mt-6 text-gray-900 dark:text-white" {...props} />
          ),

          h2: ({ node, ...props }) => (
            <h2 className="text-xl font-bold mb-3 mt-5 text-gray-900 dark:text-white" {...props} />
          ),

          h3: ({ node, ...props }) => (
            <h3 className="text-lg font-semibold mb-2 mt-4 text-gray-800 dark:text-white" {...props} />
          ),

          h4: ({ node, ...props }) => (
            <h4 className="text-base font-semibold mb-2 mt-3 text-gray-800 dark:text-white" {...props} />
          ),

          p: ({ node, ...props }) => (
            <p className="mb-3 text-gray-700 dark:text-white leading-relaxed" {...props} />
          ),
          
          // List components
          ul: ({ node, ...props }) => (
            <ul className="list-disc ml-6 mb-3 space-y-1.5" {...props} />
          ),

          ol: ({ node, ...props }) => (
            <ol className="list-decimal ml-6 mb-3 space-y-1.5" {...props} />
          ),

          li: ({ node, ...props }) => (
            <li className="text-gray-700 dark:text-white leading-relaxed" {...props} />
          ),

          // Emphasis components
          strong: ({ node, ...props }) => (
            <strong className="font-semibold text-gray-900 dark:text-white" {...props} />
          ),

          em: ({ node, ...props }) => (
            <em className="italic text-gray-700 dark:text-white" {...props} />
          ),
          
          // Code components
          code: ({ node, inline, ...props }) =>
            inline ? (
              <code
                className="bg-gray-100 dark:bg-gray-800 px-1.5 py-0.5 rounded text-xs font-mono text-red-600 dark:text-red-400"
                {...props}
              />
            ) : (
              <code
                className="block bg-gray-100 dark:bg-gray-800 p-4 rounded-lg overflow-x-auto text-xs font-mono dark:text-white"
                {...props}
              />
            ),

          pre: ({ node, ...props }) => (
            <pre className="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto mb-4" {...props} />
          ),

          // Quote component
          blockquote: ({ node, ...props }) => (
            <blockquote
              className="border-l-4 border-blue-500 pl-4 py-2 italic text-gray-600 dark:text-white bg-blue-50 dark:bg-blue-900/30 rounded-r mb-4"
              {...props}
            />
          ),
          
          // Link component
          a: ({ node, ...props }) => (
            <a 
              className="text-blue-600 hover:text-blue-800 underline"
              target="_blank"
              rel="noopener noreferrer"
              {...props} 
            />
          ),
          
          // Horizontal rule
          hr: ({ node, ...props }) => (
            <hr className="my-6 border-t-2 border-gray-300" {...props} />
          ),
          
          // Break
          br: ({ node, ...props }) => (
            <br className="my-1" {...props} />
          ),
        }}
      >
        {processContent(content)}
      </ReactMarkdown>
    </div>
  );
};

export default MarkdownRenderer;