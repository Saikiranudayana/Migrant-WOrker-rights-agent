"use client";

import { useState, useRef, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { api, ChatMessage } from "../../services/api";

const LANGUAGES = [
  { code: "en", label: "English" },
  { code: "hi", label: "हिंदी" },
  { code: "kn", label: "ಕನ್ನಡ" },
  { code: "ta", label: "தமிழ்" },
  { code: "te", label: "తెలుగు" },
  { code: "bn", label: "বাংলা" },
  { code: "or", label: "ଓଡ଼ିଆ" },
];

const SUGGESTED = [
  "What is the minimum wage in Karnataka?",
  "How do I register on e-Shram?",
  "What are my rights if I'm not paid on time?",
  "What safety gear must my employer provide?",
  "How do I claim EPFO benefits?",
  "What does the BOCW Act cover?",
];

interface Message {
  role: "user" | "assistant";
  content: string;
  sources?: { title: string; url: string; excerpt: string }[];
  loading?: boolean;
}

function ChatPageInner() {
  const searchParams = useSearchParams();
  const initialQ = searchParams.get("q") || "";
  const initialTopic = searchParams.get("topic") || "";

  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content: initialTopic
        ? `Hello! I can help you with rights and entitlements for **${initialTopic}**. What would you like to know?`
        : "Hello! I am ShramMitra AI. I can answer questions about your rights as a worker in India — wages, safety, contracts, schemes and more. How can I help you today?",
    },
  ]);
  const [input, setInput] = useState(initialQ);
  const [language, setLanguage] = useState("en");
  const [sessionId, setSessionId] = useState<string | undefined>(undefined);
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Auto-submit if URL has ?q=
  useEffect(() => {
    if (initialQ) {
      handleSend(initialQ);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function handleSend(text?: string) {
    const query = (text ?? input).trim();
    if (!query || loading) return;

    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: query }]);
    setLoading(true);

    // Add a loading bubble
    setMessages((prev) => [...prev, { role: "assistant", content: "", loading: true }]);

    try {
      const res = await api.sendMessage({
        message: query,
        language,
        session_id: sessionId,
      });

      if (res.session_id) setSessionId(res.session_id);

      setMessages((prev) => {
        const updated = [...prev];
        updated[updated.length - 1] = {
          role: "assistant",
          content: res.response,
          sources: res.sources,
          loading: false,
        };
        return updated;
      });
    } catch {
      setMessages((prev) => {
        const updated = [...prev];
        updated[updated.length - 1] = {
          role: "assistant",
          content: "Sorry, I could not process your request. Please try again.",
          loading: false,
        };
        return updated;
      });
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  return (
    <div className="flex flex-col h-screen bg-slate-950 text-white">

      {/* ── Top bar ── */}
      <header className="flex items-center justify-between px-4 py-3 bg-blue-950 border-b border-white/10 flex-shrink-0">
        <div className="flex items-center gap-3">
          <Link href="/" className="text-blue-300 hover:text-white text-sm">← Back</Link>
          <div className="flex items-center gap-2">
            <span className="text-xl">⚖️</span>
            <div>
              <div className="font-bold text-sm leading-tight">ShramMitra AI</div>
              <div className="text-xs text-blue-300">Worker Rights Assistant</div>
            </div>
          </div>
        </div>

        {/* Language picker */}
        <select
          value={language}
          onChange={(e) => setLanguage(e.target.value)}
          className="text-sm bg-white/10 border border-white/20 rounded-lg px-3 py-1.5 text-white focus:outline-none focus:ring-2 focus:ring-blue-400"
        >
          {LANGUAGES.map((l) => (
            <option key={l.code} value={l.code} className="bg-slate-900">
              {l.label}
            </option>
          ))}
        </select>
      </header>

      {/* ── Messages ── */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">

        {/* Suggested questions — shown only at start */}
        {messages.length === 1 && (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mb-4">
            {SUGGESTED.map((q) => (
              <button
                key={q}
                onClick={() => handleSend(q)}
                className="text-left text-xs bg-white/8 hover:bg-white/15 border border-white/10 rounded-lg px-3 py-2 text-blue-200 transition"
              >
                {q}
              </button>
            ))}
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
            {msg.role === "assistant" && (
              <div className="w-7 h-7 rounded-full bg-blue-600 flex items-center justify-center text-sm flex-shrink-0 mr-2 mt-1">
                ⚖️
              </div>
            )}
            <div className={`max-w-[80%] ${msg.role === "user" ? "max-w-[70%]" : ""}`}>
              <div
                className={`rounded-2xl px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap ${
                  msg.role === "user"
                    ? "bg-blue-600 text-white rounded-tr-sm"
                    : "bg-slate-800 text-gray-100 rounded-tl-sm"
                }`}
              >
                {msg.loading ? (
                  <span className="flex gap-1 items-center h-5">
                    <span className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                    <span className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                    <span className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
                  </span>
                ) : (
                  msg.content
                )}
              </div>

              {/* Source citations */}
              {msg.sources && msg.sources.length > 0 && (
                <div className="mt-2 space-y-1">
                  <div className="text-xs text-blue-400 font-medium pl-1">Sources:</div>
                  {msg.sources.map((s, si) => (
                    <a
                      key={si}
                      href={s.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="block text-xs bg-slate-700/60 hover:bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 transition"
                    >
                      <div className="font-medium text-blue-300 truncate">{s.title}</div>
                      {s.excerpt && (
                        <div className="text-gray-400 mt-0.5 line-clamp-2">{s.excerpt}</div>
                      )}
                    </a>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      {/* ── Input bar ── */}
      <div className="border-t border-white/10 bg-slate-900 px-4 py-3 flex-shrink-0">
        <div className="flex gap-2 items-end max-w-3xl mx-auto">
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about your rights, wages, safety, schemes..."
            rows={1}
            className="flex-1 bg-slate-800 border border-slate-600 focus:border-blue-500 rounded-xl px-4 py-3 text-sm text-white placeholder-gray-500 resize-none outline-none transition max-h-32 overflow-y-auto"
            style={{ fieldSizing: "content" } as React.CSSProperties}
            disabled={loading}
          />
          <button
            onClick={() => handleSend()}
            disabled={loading || !input.trim()}
            className="flex-shrink-0 w-11 h-11 bg-blue-600 hover:bg-blue-500 disabled:bg-slate-700 disabled:cursor-not-allowed rounded-xl flex items-center justify-center transition"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
            </svg>
          </button>
        </div>
        <p className="text-center text-xs text-gray-600 mt-2">
          Based on official Indian labour laws · Not a substitute for legal advice
        </p>
      </div>
    </div>
  );
}

export default function ChatPage() {
  return (
    <Suspense>
      <ChatPageInner />
    </Suspense>
  );
}
