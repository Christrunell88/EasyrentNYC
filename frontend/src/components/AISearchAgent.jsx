import React, { useState, useRef, useEffect, useMemo } from 'react';
import { MessageCircle, X, Send, Loader2, User, Phone, Lock } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import axios from '../utils/axiosConfig';
import { API } from '../App';
import useAuthStore from '../store/authStore';
import { useNavigate, useLocation } from 'react-router-dom';

const AISearchAgent = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: "Hi! 👋 I'm Chris. What kind of apartment are you looking for today?"
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  
  const user = useAuthStore((state) => state.user);
  const navigate = useNavigate();
  const location = useLocation();

  // Dynamic quick questions based on current page/context
  const quickQuestions = useMemo(() => {
    const path = location.pathname.toLowerCase();
    const searchParams = new URLSearchParams(location.search);
    const neighborhood = searchParams.get('neighborhood');
    
    // Base questions
    const baseQuestions = [
      { text: "Studios under $4,500", priority: 1 },
      { text: "2BR with doorman", priority: 2 },
      { text: "Pet-friendly options", priority: 3 },
      { text: "What's new this week?", priority: 4 },
    ];
    
    // Context-aware questions
    if (path.includes('chelsea') || neighborhood === 'Chelsea') {
      return ["More in Chelsea", "Chelsea with balcony"];
    }
    if (path.includes('hudson') || neighborhood === 'Hudson Yards') {
      return ["More in Hudson Yards", "Hudson Yards 1BR"];
    }
    if (path.includes('soho') || neighborhood === 'SoHo') {
      return ["More in SoHo", "SoHo lofts"];
    }
    if (path.includes('financial') || neighborhood === 'Financial District') {
      return ["More in FiDi", "FiDi with views"];
    }
    if (path.includes('brooklyn') || neighborhood === 'Brooklyn') {
      return ["More in Brooklyn", "Brooklyn 2BR"];
    }
    if (path.includes('west-village') || neighborhood === 'West Village') {
      return ["More in West Village", "West Village studios"];
    }
    if (path.includes('midtown') || neighborhood === 'Midtown') {
      return ["More in Midtown", "Midtown luxury"];
    }
    
    // Check for unit detail page
    if (path.includes('/unit/')) {
      return ["Similar apartments", "Schedule a viewing"];
    }
    
    // Check for dashboard/browsing
    if (path.includes('/dashboard')) {
      return ["Best deals today", "Newest listings"];
    }
    
    // Default: show top 2 most useful
    return ["Studios under $4,500", "What's available?"];
  }, [location]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (isOpen && inputRef.current && user) {
      inputRef.current.focus();
    }
  }, [isOpen, user]);

  const handleSend = async () => {
    if (!input.trim() || isLoading || !user) return;

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
        content: "I apologize, but I'm having trouble right now. Please contact me directly:\n\n📞 (646) 408-8048\n📧 placesfirm@gmail.com"
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
      {/* Dark Overlay with Blur */}
      {isOpen && (
        <div 
          className="fixed inset-0 z-40 bg-black/50 backdrop-blur-sm transition-opacity duration-300"
          onClick={() => setIsOpen(false)}
          data-testid="ai-chat-overlay"
        />
      )}

      {/* Floating Button with Label */}
      <div className="fixed bottom-6 right-6 z-50 flex flex-col items-end gap-2">
        {!isOpen && (
          <span className="bg-slate-800/90 text-[#7EB8DA] text-sm px-3 py-1.5 rounded-full shadow-lg animate-pulse font-philosopher tracking-wide">
            Ask Chris
          </span>
        )}
        <button
          onClick={() => setIsOpen(!isOpen)}
          className={`w-14 h-14 rounded-full shadow-lg transition-all duration-300 flex items-center justify-center ${
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
      </div>

      {/* Chat Window */}
      {isOpen && (
        <div 
          className="fixed bottom-24 right-6 z-50 w-[380px] h-[520px] bg-slate-900 rounded-2xl shadow-2xl border border-slate-700 flex flex-col overflow-hidden"
          data-testid="ai-chat-window"
        >
          {/* Header - Compact */}
          <div className="bg-gradient-to-r from-slate-800 to-slate-900 px-3 py-2 border-b border-slate-700">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="w-6 h-6 rounded-full bg-gradient-to-r from-[#D4AF37] to-[#B8960C] flex items-center justify-center text-slate-900 font-bold text-xs">
                  C
                </div>
                <span className="text-white font-medium text-sm">Chris</span>
                <span className="w-2 h-2 bg-green-500 rounded-full"></span>
              </div>
              <button
                onClick={() => setIsOpen(false)}
                className="text-slate-400 hover:text-white transition-colors p-1"
                title="Minimize"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Not Logged In State */}
          {!user ? (
            <div className="flex-1 flex flex-col items-center justify-center p-6 text-center">
              <div className="w-16 h-16 rounded-full bg-slate-800 flex items-center justify-center mb-4">
                <Lock className="w-8 h-8 text-[#D4AF37]" />
              </div>
              <h3 className="text-white font-semibold text-lg mb-2">Sign In to Chat with Chris</h3>
              <p className="text-slate-400 text-sm mb-6">
                Create a free account to get personalized apartment recommendations from Chris.
              </p>
              <Button
                onClick={() => {
                  setIsOpen(false);
                  navigate('/auth');
                }}
                className="bg-[#D4AF37] hover:bg-[#E5C158] text-slate-900 font-semibold px-6"
              >
                Sign In / Sign Up Free
              </Button>
              <p className="text-slate-500 text-xs mt-4">
                Or call Chris: <a href="tel:6464088048" className="text-[#D4AF37]">(646) 408-8048</a>
              </p>
            </div>
          ) : (
            <>
              {/* Messages */}
              <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {messages.map((msg, idx) => (
                  <div
                    key={idx}
                    className={`flex gap-2 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    {msg.role === 'assistant' && (
                      <div className="w-8 h-8 rounded-full bg-[#D4AF37]/20 flex items-center justify-center flex-shrink-0 text-[#D4AF37] font-bold text-sm">
                        C
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
                    <div className="w-8 h-8 rounded-full bg-[#D4AF37]/20 flex items-center justify-center text-[#D4AF37] font-bold text-sm">
                      C
                    </div>
                    <div className="bg-slate-800 rounded-2xl px-4 py-3">
                      <Loader2 className="w-5 h-5 text-[#D4AF37] animate-spin" />
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>

              {/* Quick Questions - Horizontal Scrollable */}
              {messages.length <= 2 && (
                <div className="px-3 py-2 border-t border-slate-700/50 bg-slate-900/50">
                  <div className="flex gap-2 overflow-x-auto scrollbar-hide pb-1" style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}>
                    {quickQuestions.map((q, idx) => (
                      <button
                        key={idx}
                        onClick={() => {
                          setInput(q);
                          setTimeout(() => handleSend(), 100);
                        }}
                        className="text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 px-3 py-1.5 rounded-full transition-colors border border-slate-600 whitespace-nowrap flex-shrink-0"
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
                  Need more help? Call Chris: 
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
                    placeholder="Ask Chris about apartments..."
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
            </>
          )}
        </div>
      )}
    </>
  );
};

export default AISearchAgent;
