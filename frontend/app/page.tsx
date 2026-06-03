'use client';

import { useState } from "react";
import { Plus } from "lucide-react";

import { ChatInterface } from "../components/chat/ChatInterface";
import { Message } from "../components/types";
import { ChatHeader } from "../components/layout/ChatHeader";
import { Sidebar } from "../components/layout/Sidebar";

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [presetQuestion, setPresetQuestion] = useState<string | null>(null);
  const [sessionKey, setSessionKey] = useState(0);

  const appendMessage = (message: Message) => {
    setMessages((prev) => [...prev, message]);
  };

  const startNewSession = () => {
    setMessages([]);
    setPresetQuestion(null);
    setSessionKey((prev) => prev + 1);
  };

  return (
    <div className="flex h-screen starfield overflow-hidden">
      {/* Sidebar — desktop only */}
      <Sidebar onNewSession={startNewSession} hasMessages={messages.length > 0} />

      {/* Main content */}
      <div className="flex-1 flex flex-col min-w-0 bg-command-bg/90">
        {/* Mobile top bar */}
        <div className="md:hidden shrink-0 flex items-center justify-between px-4 py-3 border-b border-command-border bg-command-panel/80">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-md bg-command-accent/10 border border-command-accent/30 flex items-center justify-center">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"
                strokeLinecap="round" strokeLinejoin="round" className="w-3.5 h-3.5 text-command-accent">
                <path d="M4 20L12 4L20 20" />
                <line x1="7" y1="14" x2="17" y2="14" />
              </svg>
            </div>
            <span className="text-sm font-semibold text-white tracking-wide">MF Assistant</span>
          </div>
          <button
            type="button"
            onClick={startNewSession}
            className="flex items-center gap-1 font-mono text-[9px] tracking-widest text-command-accent uppercase px-2.5 py-1.5 rounded border border-command-accent/30 hover:bg-command-accent/10 transition-all"
          >
            <Plus className="w-3 h-3" />
            NEW
          </button>
        </div>

        {/* Desktop header */}
        <div className="hidden md:block">
          <ChatHeader />
        </div>

        {/* Chat area */}
        <main className="flex-1 overflow-hidden flex flex-col min-h-0">
          <ChatInterface
            key={sessionKey}
            messages={messages}
            onAppendMessage={appendMessage}
            presetQuestion={presetQuestion}
            onPresetConsumed={() => setPresetQuestion(null)}
          />
        </main>
      </div>
    </div>
  );
}
