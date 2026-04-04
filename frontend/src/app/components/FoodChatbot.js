import React, { useState, useEffect, useRef } from 'react';

/**
 * FoodChatbot Component
 * 
 * Provides a conversational interface for food and nutrition queries.
 * Features:
 * - Real-time chat with Groq-powered AI
 * - Multi-language support
 * - Message history
 * - Loading states and error handling
 */

export default function FoodChatbot({ isOpen, onClose, token }) {
  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      type: 'bot',
      text: 'Hi! 👋 I\'m Shabari, your food and nutrition assistant. Ask me about any food, recipes, calories, or meal suggestions!',
      timestamp: new Date()
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const messagesEndRef = useRef(null);

  // Auto-scroll to latest message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const sendMessage = async (e) => {
    e.preventDefault();
    
    if (!input.trim()) return;
    
    const userMessage = input.trim();
    setInput('');
    setError(null);

    // Add user message to chat
    const newUserMessage = {
      id: `user-${Date.now()}`,
      type: 'user',
      text: userMessage,
      timestamp: new Date()
    };
    
    setMessages(prev => [...prev, newUserMessage]);
    setIsLoading(true);

    try {
      // Call backend chat endpoint
      const apiUrl = `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5001'}/api/chat`;
      console.log('Sending request to:', apiUrl);
      
      const response = await fetch(apiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ message: userMessage })
      });

      // Handle non-OK responses
      if (!response.ok) {
        const contentType = response.headers.get('content-type');
        let errorMessage = `API Error (${response.status}): `;
        
        try {
          if (contentType?.includes('application/json')) {
            const errorData = await response.json();
            errorMessage += errorData.error || errorData.message || 'Unknown error';
          } else {
            const text = await response.text();
            errorMessage += text.substring(0, 100) || 'Server returned non-JSON response';
          }
        } catch (parseErr) {
          errorMessage += 'Failed to parse error response';
        }
        
        throw new Error(errorMessage);
      }

      const data = await response.json();
      
      // Add bot message to chat
      const botMessage = {
        id: `bot-${Date.now()}`,
        type: 'bot',
        text: data.response,
        timestamp: new Date()
      };
      
      setMessages(prev => [...prev, botMessage]);
    } catch (err) {
      console.error('Chat error:', err);
      setError(err.message);
      
      // Add error message to chat
      const errorMessage = {
        id: `error-${Date.now()}`,
        type: 'error',
        text: `Sorry, I encountered an error: ${err.message}`,
        timestamp: new Date()
      };
      
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
      scrollToBottom();
    }
  };

  const clearHistory = async () => {
    if (!window.confirm('Clear chat history?')) return;
    
    try {
      const apiUrl = `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5001'}/api/chat/clear`;
      
      const response = await fetch(apiUrl, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error(`Failed to clear history (${response.status})`);
      }
      
      // Reset messages to welcome message
      setMessages([
        {
          id: 'welcome',
          type: 'bot',
          text: 'Hi! 👋 I\'m Shabari, your food and nutrition assistant. Ask me about any food, recipes, calories, or meal suggestions!',
          timestamp: new Date()
        }
      ]);
      setError(null);
    } catch (err) {
      setError('Failed to clear history');
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-40 flex items-end md:items-center md:justify-end bg-black/30 backdrop-blur-sm" onClick={onClose}>
      <div
        className="w-full h-screen md:h-auto md:w-96 bg-white rounded-t-3xl md:rounded-2xl shadow-2xl animate-slide-up md:mb-4 md:mr-4 overflow-hidden flex flex-col md:max-h-[90vh]"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 md:p-5 border-b border-slate-200 bg-gradient-to-r from-blue-50 to-blue-100">
          <div className="flex-1 min-w-0">
            <h2 className="text-xl md:text-2xl font-bold text-slate-900">💬 Shabari</h2>
            <p className="text-slate-600 text-xs md:text-sm">Food & Nutrition Assistant</p>
          </div>
          <div className="flex gap-1 md:gap-2 ml-2 flex-shrink-0">
            {messages.length > 1 && (
              <button
                onClick={clearHistory}
                className="p-2 hover:bg-slate-200 rounded-lg transition active:scale-95"
                title="Clear history"
              >
                🗑️
              </button>
            )}
            <button
              onClick={onClose}
              className="p-2 text-2xl text-slate-300 hover:text-slate-600 hover:bg-slate-200 rounded-lg transition active:scale-95"
              title="Close"
            >
              ✕
            </button>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto bg-gradient-to-b from-slate-50 to-white p-3 md:p-4 space-y-3 scroll-smooth">
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex ${msg.type === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[85%] md:max-w-sm px-3 py-2 md:px-4 md:py-2 rounded-2xl text-sm leading-relaxed ${
                  msg.type === 'user'
                    ? 'bg-gradient-to-br from-blue-500 to-blue-600 text-white rounded-br-none shadow-md'
                    : msg.type === 'error'
                    ? 'bg-red-100 text-red-800 border border-red-300 rounded-bl-none'
                    : 'bg-white text-slate-700 border border-slate-200 rounded-bl-none shadow-sm'
                }`}
              >
                <p className="whitespace-pre-wrap break-words">{msg.text}</p>
                <span className={`text-xs mt-1 block opacity-70 ${msg.type === 'user' ? 'text-blue-100' : 'text-slate-500'}`}>
                  {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </span>
              </div>
            </div>
          ))}
          
          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-white border border-slate-200 px-4 py-2 rounded-2xl text-slate-600 rounded-bl-none shadow-sm">
                <div className="flex gap-1">
                  <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                  <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></div>
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        {/* Input Form */}
        <form onSubmit={sendMessage} className="border-t border-slate-200 bg-white p-3 md:p-4 space-y-2 flex-shrink-0">
          <div className="flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about food..."
              className="flex-1 px-4 py-2.5 md:py-3 text-sm md:text-base border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition"
              disabled={isLoading}
            />
            <button
              type="submit"
              disabled={isLoading || !input.trim()}
              className="px-4 md:px-6 py-2.5 md:py-3 bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white font-semibold rounded-xl transition-all active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed shadow-md hover:shadow-lg"
            >
              {isLoading ? '...' : 'Send'}
            </button>
          </div>
          {error && (
            <p className="text-xs text-red-600 px-2">{error}</p>
          )}
        </form>
      </div>
    </div>
  );
}
