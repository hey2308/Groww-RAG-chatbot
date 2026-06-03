'use client';

import { Sun } from "lucide-react";

export function ChatHeader() {
  return (
    <header className="h-14 shrink-0 border-b border-command-border bg-command-panel/80 backdrop-blur-sm px-5 flex items-center justify-between">
      {/* Left: badge + title */}
      <div className="flex items-center gap-2.5">
        <span className="font-mono text-[10px] font-bold text-command-accent bg-command-accent/10 px-1.5 py-0.5 rounded border border-command-accent/25 tracking-wider">
          [CMD]
        </span>
        <h1 className="text-[13px] font-semibold text-white tracking-wide">
          Mutual Fund FAQ Assistant
        </h1>
      </div>

      {/* Right: sun icon + avatar */}
      <div className="flex items-center gap-3">
        <button
          type="button"
          aria-label="Toggle theme"
          className="p-1.5 rounded-lg text-command-muted hover:text-white hover:bg-command-surface transition-all"
        >
          <Sun className="w-4 h-4" />
        </button>

        {/* Avatar circle */}
        <div className="w-8 h-8 rounded-full border border-command-border bg-command-surface overflow-hidden flex items-center justify-center shrink-0">
          <svg viewBox="0 0 32 32" fill="none" className="w-full h-full">
            <rect width="32" height="32" fill="#1E293B" />
            <circle cx="16" cy="13" r="5" fill="#64748B" />
            <ellipse cx="16" cy="26" rx="9" ry="6" fill="#64748B" />
          </svg>
        </div>
      </div>
    </header>
  );
}

export default ChatHeader;
