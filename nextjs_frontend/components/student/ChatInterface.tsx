'use client';

import { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import 'katex/dist/katex.min.css';

import { ragQuery } from '@/lib/api';
import type { ChatMessage } from '@/lib/types';

interface ChatInterfaceProps {
  selectedMaterial: string | null;
}

/**
 * Chat Interface Component
 * AI tutor chat powered by RAG
 */
export default function ChatInterface({ selectedMaterial }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Clear messages when material changes
  useEffect(() => {
    setMessages([]);
  }, [selectedMaterial]);

  // Handle send message
  const handleSend = async () => {
    if (!input.trim() || !selectedMaterial || loading) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const response = await ragQuery({
        query: input,
        doc_id: selectedMaterial,
        top_k: 4,
      });

      const assistantMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.answer,
        timestamp: new Date(),
        chunks: response.retrieved_chunks,
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error: any) {
      console.error('Chat error:', error);
      
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `Sorry, I encountered an error: ${error.message || 'Unknown error'}. Please try again.`,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  // Handle Enter key
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="panel h-full flex flex-col">
      {/* Header */}
      <div className="panel-header">
        <h3 className="font-semibold text-aub-black">
          💬 AI Tutor
          {selectedMaterial && (
            <span className="text-xs font-normal text-gray-500 ml-2">
              · {selectedMaterial}
            </span>
          )}
        </h3>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 custom-scrollbar">
        {messages.length === 0 && (
          <div className="text-center text-gray-500 mt-8">
            {selectedMaterial ? (
              <>
                <p className="mb-2">👋 Hello! I&apos;m your AI tutor.</p>
                <p className="text-sm">Ask me anything about <strong>{selectedMaterial}</strong></p>
              </>
            ) : (
              <p>Select a material from the left to start chatting</p>
            )}
          </div>
        )}

        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[85%] rounded-2xl px-4 py-2.5 ${
                msg.role === 'user'
                  ? 'bg-aub-red text-white rounded-tr-sm'
                  : 'bg-gray-100 text-gray-900 rounded-tl-sm'
              }`}
            >
              <div className="prose prose-sm max-w-none">
                {msg.role === 'user' ? (
                  <p className="text-sm m-0">{msg.content}</p>
                ) : (
                  <ReactMarkdown
                    remarkPlugins={[remarkGfm, remarkMath]}
                    rehypePlugins={[rehypeKatex]}
                    components={{
                      p: ({ children }) => <p className="text-sm m-0 mb-2 last:mb-0">{children}</p>,
                      ul: ({ children }) => <ul className="text-sm my-2 ml-4">{children}</ul>,
                      ol: ({ children }) => <ol className="text-sm my-2 ml-4">{children}</ol>,
                      li: ({ children }) => <li className="text-sm">{children}</li>,
                      code: ({ inline, children }: any) =>
                        inline ? (
                          <code className="bg-gray-200 px-1 py-0.5 rounded text-xs">
                            {children}
                          </code>
                        ) : (
                          <code className="block bg-gray-800 text-gray-100 p-2 rounded text-xs">
                            {children}
                          </code>
                        ),
                    }}
                  >
                    {msg.content}
                  </ReactMarkdown>
                )}
              </div>
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="bg-gray-100 rounded-2xl rounded-tl-sm px-4 py-3 flex items-center gap-2">
              <div className="spinner"></div>
              <span className="text-sm text-gray-600">Thinking...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="p-4 border-t border-gray-200">
        <div className="flex gap-2">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={
              selectedMaterial
                ? 'Ask a question...'
                : 'Select a material first'
            }
            disabled={!selectedMaterial || loading}
            rows={2}
            className="textarea flex-1 resize-none text-sm text-gray-900"
          />
          <button
            onClick={handleSend}
            disabled={!selectedMaterial || loading || !input.trim()}
            className="btn-primary self-end px-6"
          >
            Send
          </button>
        </div>
        <p className="text-xs text-gray-500 mt-2">
          Press <kbd className="px-1 py-0.5 bg-gray-200 rounded text-xs">Enter</kbd> to send
        </p>
      </div>
    </div>
  );
}

