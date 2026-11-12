import React, { useState, useEffect, useRef } from 'react';
import api from '../api/client';
import {
  MessageSquare,
  X,
  Send,
  Sparkles,
  Bot,
  User as UserIcon,
  Copy,
  Check,
  RotateCcw,
  FileText,
  ChevronDown,
} from 'lucide-react';

export default function AIChatDrawer({ isOpen, onClose, documentId = null, documentTitle = null }) {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: documentTitle
        ? `Hello! I am your Agentra Intelligence Assistant. I have indexed **${documentTitle}**. You can ask me about approval limits, required documentation, deadlines, or compliance issues.`
        : 'Hello! I am your Agentra Intelligence Assistant. Ask me anything about your uploaded documents, compliance rules, or reimbursement policies.',
    },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [copiedIndex, setCopiedIndex] = useState(null);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const suggestedQuestions = documentId
    ? [
        'What are the manager approval thresholds?',
        'Are itemized receipts mandatory for all claims?',
        'What is the submission deadline for expenses?',
        'List all non-reimbursable expense items.',
      ]
    : [
        'What compliance rules are currently enforced?',
        'How does the 4-step agent orchestrator work?',
        'What are standard reimbursement tiers?',
      ];

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 150);
      scrollToBottom();
    }
  }, [isOpen, messages]);

  const handleSendMessage = async (textToSend = null) => {
    const text = textToSend || input.trim();
    if (!text || loading) return;

    const userMessage = { role: 'user', content: text };
    const newMessages = [...messages, userMessage];
    setMessages(newMessages);
    setInput('');
    setLoading(true);

    try {
      // Prepare history excluding the initial welcome message
      const historyToSend = newMessages
        .filter((_, idx) => idx > 0)
        .map((m) => ({ role: m.role, content: m.content }));

      const res = await api.post('/chat', {
        message: text,
        document_id: documentId,
        history: historyToSend,
      });

      const replyContent = res.data.data.reply;
      setMessages([...newMessages, { role: 'assistant', content: replyContent }]);
    } catch (err) {
      const errorMsg =
        err.response?.data?.error?.message ||
        'Unable to reach AI assistant. Please verify your connection or try again.';
      setMessages([
        ...newMessages,
        {
          role: 'assistant',
          content: `⚠️ **Error:** ${errorMsg}`,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const copyToClipboard = (text, idx) => {
    navigator.clipboard.writeText(text);
    setCopiedIndex(idx);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  const handleResetChat = () => {
    setMessages([
      {
        role: 'assistant',
        content: documentTitle
          ? `Conversation reset. Ask me anything about **${documentTitle}**.`
          : 'Conversation reset. Ask me anything about your documents or compliance rules.',
      },
    ]);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-y-0 right-0 z-50 w-full sm:w-[480px] bg-white border-l border-slate-200 shadow-2xl flex flex-col font-sans transition-all duration-300 ease-in-out">
      {/* Header */}
      <div className="h-16 px-5 border-b border-slate-100 flex items-center justify-between bg-slate-900 text-white">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-indigo-500/20 border border-indigo-400/30 flex items-center justify-center text-indigo-300">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-sm font-semibold text-white">Agentra AI Assistant</h2>
              <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-medium bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                Gemini 3.5
              </span>
            </div>
            <p className="text-[11px] text-slate-400">
              {documentTitle ? `Context: ${documentTitle.slice(0, 30)}...` : 'Enterprise Document Intelligence'}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-1">
          <button
            onClick={handleResetChat}
            title="Reset Conversation"
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <RotateCcw className="w-4 h-4" />
          </button>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Scoped Document Banner (if active) */}
      {documentTitle && (
        <div className="px-4 py-2 bg-indigo-50/70 border-b border-indigo-100/80 flex items-center justify-between text-xs">
          <div className="flex items-center gap-2 text-indigo-900 min-w-0">
            <FileText className="w-3.5 h-3.5 text-indigo-600 flex-shrink-0" />
            <span className="font-medium truncate">{documentTitle}</span>
          </div>
          <span className="text-[10px] font-semibold text-indigo-600 uppercase tracking-wider flex-shrink-0">
            Active Context
          </span>
        </div>
      )}

      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-slate-50/50">
        {messages.map((msg, index) => {
          const isUser = msg.role === 'user';
          return (
            <div key={index} className={`flex gap-3 ${isUser ? 'justify-end' : 'justify-start'}`}>
              {!isUser && (
                <div className="w-7 h-7 rounded-lg bg-indigo-600 text-white flex items-center justify-center flex-shrink-0 mt-0.5 shadow-sm">
                  <Bot className="w-4 h-4" />
                </div>
              )}

              <div
                className={`group relative max-w-[85%] rounded-2xl p-3.5 text-xs leading-relaxed ${
                  isUser
                    ? 'bg-indigo-600 text-white rounded-br-sm shadow-sm'
                    : 'bg-white text-slate-800 border border-slate-200/80 rounded-bl-sm shadow-sm'
                }`}
              >
                <div className="whitespace-pre-wrap">{msg.content}</div>

                {!isUser && (
                  <button
                    onClick={() => copyToClipboard(msg.content, index)}
                    title="Copy Answer"
                    className="absolute top-2 right-2 p-1 rounded bg-slate-100 text-slate-500 hover:text-slate-800 opacity-0 group-hover:opacity-100 transition-opacity"
                  >
                    {copiedIndex === index ? (
                      <Check className="w-3 h-3 text-emerald-600" />
                    ) : (
                      <Copy className="w-3 h-3" />
                    )}
                  </button>
                )}
              </div>

              {isUser && (
                <div className="w-7 h-7 rounded-lg bg-slate-200 text-slate-700 flex items-center justify-center flex-shrink-0 mt-0.5">
                  <UserIcon className="w-4 h-4" />
                </div>
              )}
            </div>
          );
        })}

        {/* Loading Indicator */}
        {loading && (
          <div className="flex gap-3 justify-start items-center">
            <div className="w-7 h-7 rounded-lg bg-indigo-600 text-white flex items-center justify-center flex-shrink-0 shadow-sm">
              <Bot className="w-4 h-4" />
            </div>
            <div className="bg-white border border-slate-200/80 rounded-2xl rounded-bl-sm p-3.5 shadow-sm flex items-center gap-2 text-xs text-slate-500">
              <div className="flex gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-indigo-600 animate-bounce"></span>
                <span className="w-1.5 h-1.5 rounded-full bg-indigo-600 animate-bounce [animation-delay:0.2s]"></span>
                <span className="w-1.5 h-1.5 rounded-full bg-indigo-600 animate-bounce [animation-delay:0.4s]"></span>
              </div>
              <span>Analyzing policy rules with Gemini 3.5...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Suggested Quick Questions */}
      {messages.length <= 2 && !loading && (
        <div className="px-4 py-2 bg-white border-t border-slate-100">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
            Suggested Prompts
          </p>
          <div className="flex flex-wrap gap-1.5">
            {suggestedQuestions.map((q, idx) => (
              <button
                key={idx}
                onClick={() => handleSendMessage(q)}
                className="text-[11px] text-left px-2.5 py-1 rounded-lg bg-slate-50 hover:bg-indigo-50 hover:text-indigo-700 border border-slate-200/80 text-slate-600 transition-colors"
              >
                {q}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input Form */}
      <div className="p-3 bg-white border-t border-slate-200">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSendMessage();
          }}
          className="flex items-center gap-2"
        >
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={
              documentTitle
                ? 'Ask a question about this policy...'
                : 'Ask anything about compliance, rules, or documents...'
            }
            disabled={loading}
            className="flex-1 px-3.5 py-2.5 text-xs bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 text-slate-900 placeholder:text-slate-400 disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={!input.trim() || loading}
            className="p-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white disabled:opacity-40 disabled:cursor-not-allowed transition-all shadow-sm"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
        <p className="text-[10px] text-slate-400 text-center mt-1.5">
          Grounded on extracted policy text & deterministic compliance logic
        </p>
      </div>
    </div>
  );
}
