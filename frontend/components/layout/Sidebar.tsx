'use client';

import { History, Plus } from "lucide-react";

interface SidebarProps {
  onNewSession: () => void;
  hasMessages: boolean;
}

export function Sidebar({ onNewSession }: SidebarProps) {
  return (
    <aside className="w-56 bg-command-bg border-r border-command-border flex flex-col h-full shrink-0 hidden md:flex">
      {/* ── Logo / Brand ── */}
      <div className="px-5 py-5 border-b border-command-border flex items-center gap-3">
        {/* Triangle "A" logo */}
        <div className="w-8 h-8 rounded-md bg-command-accent/10 border border-command-accent/30 flex items-center justify-center shrink-0">
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="w-4 h-4 text-command-accent"
          >
            <path d="M4 20L12 4L20 20" />
            <line x1="7" y1="14" x2="17" y2="14" />
          </svg>
        </div>
        <div className="min-w-0">
          <p className="text-[13px] font-semibold text-white tracking-wide leading-none">
            MF Assistant
          </p>
          <div className="flex items-center gap-1.5 mt-1">
            <span className="status-dot" />
            <span className="font-mono text-[9px] tracking-widest text-command-accent/80 uppercase">
              System Active
            </span>
          </div>
        </div>
      </div>

      {/* ── Nav ── */}
      <div className="flex-1 flex flex-col gap-5 px-4 py-5">
        {/* New Session */}
        <button
          type="button"
          onClick={onNewSession}
          className="btn-new-session"
        >
          <Plus className="w-3.5 h-3.5" />
          NEW_SESSION
        </button>

        {/* Archive Logs */}
        <div className="space-y-1.5">
          <p className="px-1 font-mono text-[9px] tracking-widest text-command-muted uppercase">
            Archive_Logs
          </p>
          <button
            type="button"
            className="w-full flex items-center gap-2.5 px-2.5 py-2 rounded-lg text-[11px] font-mono text-command-text hover:bg-command-surface/60 cursor-pointer transition-all text-left"
          >
            <History className="w-3.5 h-3.5 text-command-muted shrink-0" />
            <span>Recent_Data</span>
          </button>
        </div>
      </div>
    </aside>
  );
}
