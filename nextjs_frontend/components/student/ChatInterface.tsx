'use client';

import { useEffect, useRef, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import 'katex/dist/katex.min.css';

import { streamRagQuery } from '@/lib/api';
import type { ChatMessage, RAGStreamEvent } from '@/lib/types';

interface ChatInterfaceProps {
  selectedMaterial: string | null;
}

/**
 * Chat Interface Component
 * AI tutor chat powered by RAG with streaming + history
 */
export default function ChatInterface({ selectedMaterial }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const controllerRef = useRef<AbortController | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Clear messages when material changes
  useEffect(() => {
    setMessages([]);
    setError(null);
    setInput('');
    if (controllerRef.current) {
      controllerRef.current.abort();
      controllerRef.current = null;
    }
    setIsStreaming(false);
  }, [selectedMaterial]);

  const updateAssistantMessage = (
    id: string,
    updater: (msg: ChatMessage) => ChatMessage
  ) => {
    setMessages((prev) => prev.map((msg) => (msg.id === id ? updater(msg) : msg)));
  };

  // Handle send message
  const handleSend = async () => {
    if (!input.trim() || !selectedMaterial || isStreaming) return;

    const userMessage: ChatMessage = {
      id: `${Date.now()}-user`,
      role: 'user',
      content: input,
      timestamp: new Date(),
    };

    const assistantId = `${Date.now()}-assistant`;
    const assistantMessage: ChatMessage = {
      id: assistantId,
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      chunks: [],
    };

    const historyPayload = [...messages, userMessage]
      .slice(-12)
      .map(({ role, content }) => ({ role, content }));

    setMessages((prev) => [...prev, userMessage, assistantMessage]);
    setInput('');
    setError(null);
    setIsStreaming(true);

    const controller = new AbortController();
    controllerRef.current = controller;
    let accumulatedAnswer = '';

    try {
      await streamRagQuery(
        {
          query: userMessage.content,
          doc_id: selectedMaterial,
          top_k: 4,
          history: historyPayload,
        },
        (event: RAGStreamEvent) => {
          if (event.type === 'metadata') {
            updateAssistantMessage(assistantId, (msg) => ({
              ...msg,
              chunks: event.retrieved_chunks,
            }));
          } else if (event.type === 'token') {
            accumulatedAnswer += event.value;
            updateAssistantMessage(assistantId, (msg) => ({
              ...msg,
              content: accumulatedAnswer,
            }));
          } else if (event.type === 'done') {
            setIsStreaming(false);
            controllerRef.current = null;
          } else if (event.type === 'error') {
            setIsStreaming(false);
            controllerRef.current = null;
            setError(event.message || 'Something went wrong while generating a reply.');
            updateAssistantMessage(assistantId, (msg) => ({
              ...msg,
              content: 'Sorry, I hit an error while generating that response.',
            }));
          }
        },
        controller.signal
      );
    } catch (error: any) {
      if (error?.name !== 'AbortError') {
        console.error('Chat error:', error);
        setError(error?.message || 'Failed to get a response. Please try again.');
        updateAssistantMessage(assistantId, (msg) => ({
          ...msg,
          content: `Sorry, I encountered an error: ${error?.message || 'Unknown error'}. Please try again.`,
        }));
      }
    } finally {
      setIsStreaming(false);
      controllerRef.current = null;
    }
  };

  const handleStop = () => {
    if (controllerRef.current) {
      controllerRef.current.abort();
      controllerRef.current = null;
    }
    setIsStreaming(false);
  };

  // Handle Enter key
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="panel h-full flex flex-col bg-gradient-to-b from-white to-aub-beige/60">
      <div className="panel-header flex items-center justify-between">
        <div>
          <p className="text-xs uppercase text-gray-500 tracking-wide">AI Tutor</p>
          <h3 className="font-semibold text-aub-black">
            {selectedMaterial ? `Chat about ${selectedMaterial}` : 'Select a material to start'}
          </h3>
          <p className="text-xs text-gray-500">
            Answers stay grounded in your uploaded materials with citations.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span
            className={`px-3 py-1 rounded-full text-xs ${
              selectedMaterial ? 'bg-emerald-100 text-emerald-700' : 'bg-gray-200 text-gray-600'
            }`}
          >
            {selectedMaterial ? 'Ready' : 'Pick a material'}
          </span>
          {isStreaming && (
            <button
              onClick={handleStop}
              className="text-xs px-3 py-1 rounded-full border border-aub-red text-aub-red hover:bg-aub-red hover:text-white transition-colors"
            >
              Stop
            </button>
          )}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-3 space-y-4 custom-scrollbar bg-white/60">
        {messages.length === 0 && (
          <div className="text-center text-gray-600 rounded-xl border border-dashed border-gray-300 bg-white/70 p-6">
            {selectedMaterial ? (
              <>
                <p className="mb-2 font-semibold text-aub-black">Hello! I&apos;m your AI tutor.</p>
                <p className="text-sm">
                  Ask me anything about <strong>{selectedMaterial}</strong> and I&apos;ll cite the
                  relevant sections.
                </p>
              </>
            ) : (
              <p className="text-sm">Choose a material on the left to begin.</p>
            )}
          </div>
        )}

        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`flex gap-3 max-w-[85%] ${
                msg.role === 'user' ? 'flex-row-reverse text-right' : ''
              }`}
            >
              <div
                className={`h-8 w-8 rounded-full flex items-center justify-center text-xs font-semibold ${
                  msg.role === 'user' ? 'bg-aub-red text-white' : 'bg-gray-200 text-gray-700'
                }`}
              >
                {msg.role === 'user' ? 'You' : 'AI'}
              </div>
              <div
                className={`rounded-2xl px-4 py-3 shadow-sm ${
                  msg.role === 'user'
                    ? 'bg-aub-red text-white'
                    : 'bg-gray-50 text-gray-900 border border-gray-200'
                }`}
              >
                <div className="prose prose-sm max-w-none">
                  {msg.role === 'user' ? (
                    <p className="text-sm m-0 whitespace-pre-wrap">{msg.content}</p>
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
                            <code className="bg-gray-200 px-1 py-0.5 rounded text-xs text-gray-800">
                              {children}
                            </code>
                          ) : (
                            <code className="block bg-gray-900 text-gray-100 p-2 rounded text-xs whitespace-pre-wrap">
                              {children}
                            </code>
                          ),
                      }}
                    >
                      {msg.content || (isStreaming ? '...' : '')}
                    </ReactMarkdown>
                  )}
                </div>

                {msg.role === 'assistant' && msg.chunks && msg.chunks.length > 0 && (
                  <div className="mt-3 flex flex-wrap gap-2">
                    {msg.chunks.slice(0, 4).map((chunk) => (
                      <span
                        key={chunk.chunk_id}
                        className="inline-flex items-center gap-1 rounded-full bg-white border border-gray-200 px-2 py-1 text-[11px] text-gray-700"
                      >
                        <span className="h-1.5 w-1.5 rounded-full bg-aub-red" />
                        {chunk.doc_id || 'source'} · {chunk.chunk_id}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}

        {isStreaming && (
          <div className="flex items-center gap-2 text-sm text-gray-600">
            <span className="h-2 w-2 rounded-full bg-aub-red animate-pulse" />
            AI is thinking...
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <div className="p-4 border-t border-gray-200 bg-white">
        {error && (
          <div className="alert-error text-xs mb-2">
            <p>{error}</p>
          </div>
        )}
        <div className="flex gap-3">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={
              selectedMaterial
                ? 'Ask a question...'
                : 'Select a material first'
            }
            disabled={!selectedMaterial || isStreaming}
            rows={2}
            className="textarea flex-1 resize-none text-sm text-gray-900 bg-gray-50 border border-gray-200"
          />
          <button
            onClick={handleSend}
            disabled={!selectedMaterial || isStreaming || !input.trim()}
            className="btn-primary self-end px-6 shadow-sm"
          >
            Send
          </button>
        </div>
        <p className="text-xs text-gray-500 mt-2">
          Press <kbd className="px-1 py-0.5 bg-gray-200 rounded text-xs">Enter</kbd> to send,{' '}
          <kbd className="px-1 py-0.5 bg-gray-200 rounded text-xs">Shift + Enter</kbd> for a new line
        </p>
      </div>
    </div>
  );
}
