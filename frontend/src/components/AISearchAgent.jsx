import React, { useState, useRef, useEffect } from 'react';
import { MessageCircle, X, Send, Loader2, Bot, User, Phone, Mail } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import axios from '../utils/axiosConfig';
import { API } from '../App';

const AISearchAgent = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: "Hi! 👋 I'm your NoFeesApts AI assistant. I can help you find no-fee apartments in NYC, NJ, and PA. What are you looking for today?\n\nTry asking me:\n• \"Show me studios under $4,000 in Manhattan\"\n• \"What's available in Hudson Yards?\"\n• \"I need a 2BR pet-friendly apartment\""
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen]);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage = input.trim();
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setIsLoading(true);

    try {
      const response = await axios.post(`${API}/ai-search`, {
        message: userMessage,
        session_id: sessionId
      }, { withCredentials: true });

      setSessionId(response.data.session_id);
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: response.data.response,
        unitsFound: response.data.units_found
      }]);
    } catch (error) {
      console.error('AI Search error:', error);
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: "I apologize, but I'm having trouble right now. Please contact Chris directly:\n\n📞 (646) 408-8048\n📧 placesfirm@gmail.com"
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const quickQuestions = [
    "Studios under $4,500",
    "2BR in Chelsea",
    "Pet-friendly apartments",
    "What neighborhoods do you have?"
  ];

  return (
    <>
      {/* Floating Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`fixed bottom-6 right-6 z-50 w-14 h-14 rounded-full shadow-lg transition-all duration-300 flex items-center justify-center ${
          isOpen 
            ? 'bg-slate-800 hover:bg-slate-700' 
            : 'bg-gradient-to-r from-[#D4AF37] to-[#B8960C] hover:from-[#E5C158] hover:to-[#C9A71D]'
        }`}
        data-testid="ai-chat-toggle"
      >
        {isOpen ? (
          <X className="w-6 h-6 text-white" />
        ) : (
          <MessageCircle className="w-6 h-6 text-slate-900" />
        )}
      </button>

      {/* Chat Window */}
      {isOpen && (
        <div 
          className="fixed bottom-24 right-6 z-50 w-[380px] h-[520px] bg-slate-900 rounded-2xl shadow-2xl border border-slate-700 flex flex-col overflow-hidden"
          data-testid="ai-chat-window"
        >
          {/* Header */}
          <div className="bg-gradient-to-r from-slate-800 to-slate-900 px-4 py-3 border-b border-slate-700">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-gradient-to-r from-[#D4AF37] to-[#B8960C] flex items-center justify-center">
                <Bot className="w-5 h-5 text-slate-900" />
              </div>
              <div>
                <h3 className="text-white font-semibold text-sm">NoFeesApts AI Assistant</h3>
                <p className="text-slate-400 text-xs">Powered by AI • Always free to chat</p>
              </div>
            </div>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.map((msg, idx) => (
              <div
                key={idx}
                className={`flex gap-2 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                {msg.role === 'assistant' && (
                  <div className="w-8 h-8 rounded-full bg-[#D4AF37]/20 flex items-center justify-center flex-shrink-0">
                    <Bot className="w-4 h-4 text-[#D4AF37]" />
                  </div>
                )}
                <div
                  className={`max-w-[80%] rounded-2xl px-4 py-2.5 ${
                    msg.role === 'user'
                      ? 'bg-[#D4AF37] text-slate-900'
                      : 'bg-slate-800 text-slate-200'
                  }`}
                >
                  <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                  {msg.unitsFound > 0 && (
                    <p className="text-xs mt-2 opacity-70">
                      Found {msg.unitsFound} matching units
                    </p>
                  )}
                </div>
                {msg.role === 'user' && (
                  <div className="w-8 h-8 rounded-full bg-slate-700 flex items-center justify-center flex-shrink-0">
                    <User className="w-4 h-4 text-slate-300" />
                  </div>
                )}
              </div>
            ))}
            
            {isLoading && (
              <div className="flex gap-2 justify-start">
                <div className="w-8 h-8 rounded-full bg-[#D4AF37]/20 flex items-center justify-center">
                  <Bot className="w-4 h-4 text-[#D4AF37]" />
                </div>
                <div className="bg-slate-800 rounded-2xl px-4 py-3">
                  <Loader2 className="w-5 h-5 text-[#D4AF37] animate-spin" />
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Quick Questions */}
          {messages.length <= 2 && (
            <div className="px-4 pb-2">
              <div className="flex flex-wrap gap-2">
                {quickQuestions.map((q, idx) => (
                  <button
                    key={idx}
                    onClick={() => {
                      setInput(q);
                      setTimeout(() => handleSend(), 100);
                    }}
                    className="text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 px-3 py-1.5 rounded-full transition-colors border border-slate-700"
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Contact Info */}
          <div className="px-4 py-2 bg-slate-800/50 border-t border-slate-700">
            <p className="text-xs text-slate-400 text-center">
              Need personalized help? Contact Chris: 
              <a href="tel:6464088048" className="text-[#D4AF37] hover:underline ml-1">
                <Phone className="w-3 h-3 inline" /> (646) 408-8048
              </a>
            </p>
          </div>

          {/* Input */}
          <div className="p-3 border-t border-slate-700 bg-slate-900">
            <div className="flex gap-2">
              <Input
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Ask about apartments..."
                className="flex-1 bg-slate-800 border-slate-700 text-white placeholder:text-slate-500 focus:border-[#D4AF37] focus:ring-[#D4AF37]/20"
                disabled={isLoading}
                data-testid="ai-chat-input"
              />
              <Button
                onClick={handleSend}
                disabled={!input.trim() || isLoading}
                className="bg-[#D4AF37] hover:bg-[#E5C158] text-slate-900 px-3"
                data-testid="ai-chat-send"
              >
                <Send className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default AISearchAgent;
