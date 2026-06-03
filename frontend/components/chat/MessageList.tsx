import { Loader2, Shield } from "lucide-react";
import { Message } from "../types";
import { SourceCitation } from "./SourceCitation";
import {
  detectMessageVariant,
  formatTimestamp,
  highlightFacts,
  splitResponseContent,
} from "./messageUtils";

interface MessageListProps {
  messages: Message[];
  isLoading?: boolean;
}

/* ── Assistant: informational card ── */
function InformationalMessage({ message }: { message: Message }) {
  const { body, footer } = splitResponseContent(message.content);

  return (
    <div className="max-w-2xl w-full" style={{ animation: "slideUp 0.3s ease-out" }}>
      <div className="rounded-xl border border-command-border bg-command-surface/80 overflow-hidden">
        {/* Card header row */}
        <div className="flex flex-wrap items-center gap-x-3 gap-y-1 px-4 py-2 border-b border-command-border bg-command-panel/50">
          <span className="cmd-label">
            {message.source ? "VERIFIED_SRC_PUBLIC" : "SRC_PENDING"}
          </span>
          <span className="cmd-meta">NULL_ADVICE_POLICY</span>
          <span className="cmd-meta ml-auto">
            TIMESTAMP: {formatTimestamp(message.timestamp)}
          </span>
        </div>
        {/* Card body */}
        <div className="px-4 py-3">
          <p className="message-content">{highlightFacts(body)}</p>
          {footer ? (
            <p className="mt-2 text-xs text-command-muted font-mono">
              Last updated: {footer}
            </p>
          ) : null}
          {message.source ? (
            <div className="mt-3 pt-3 border-t border-command-border">
              <SourceCitation source={message.source} />
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}

/* ── Assistant: compliance card ── */
function ComplianceMessage({ message }: { message: Message }) {
  const { body } = splitResponseContent(message.content);

  return (
    <div className="max-w-2xl w-full" style={{ animation: "slideUp 0.3s ease-out" }}>
      <div className="rounded-xl border border-command-danger/30 bg-command-danger-bg overflow-hidden">
        {/* Red header */}
        <div className="flex items-center gap-2 px-4 py-2.5 border-b border-command-danger/20 bg-command-danger/5">
          <Shield className="w-3.5 h-3.5 text-command-danger shrink-0" />
          <span className="font-mono text-[10px] uppercase tracking-wider text-command-danger">
            COMPLIANCE_PROTOCOL_ACTIVE
          </span>
        </div>
        {/* Body */}
        <div className="px-4 py-3">
          <p className="message-content">{body}</p>
          {message.source ? (
            <div className="mt-3 pt-3 border-t border-command-danger/20">
              <SourceCitation source={message.source} variant="compliance" />
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}

/* ── Assistant: error card ── */
function ErrorMessage({ message }: { message: Message }) {
  const { body } = splitResponseContent(message.content);

  return (
    <div className="max-w-2xl w-full" style={{ animation: "slideUp 0.3s ease-out" }}>
      <div className="rounded-xl border border-command-danger/40 bg-command-danger-bg px-4 py-3">
        <p className="cmd-label text-command-danger mb-2">SYSTEM_ERROR</p>
        <p className="message-content text-command-danger/90">{body}</p>
      </div>
    </div>
  );
}

/* ── Dispatcher ── */
function AssistantMessage({ message }: { message: Message }) {
  const variant = message.variant ?? detectMessageVariant(message.content);
  if (variant === "error") return <ErrorMessage message={message} />;
  if (variant === "compliance") return <ComplianceMessage message={message} />;
  return <InformationalMessage message={message} />;
}

/* ── User bubble ── */
function UserMessage({ message }: { message: Message }) {
  return (
    <div className="max-w-xl" style={{ animation: "slideUp 0.3s ease-out" }}>
      <div className="px-4 py-2.5 rounded-2xl rounded-br-md bg-command-user border border-command-border text-command-text text-sm leading-relaxed">
        {message.content}
      </div>
    </div>
  );
}

/* ── Loading indicator ── */
function LoadingIndicator() {
  return (
    <div className="max-w-2xl w-full" style={{ animation: "fadeIn 0.5s ease-in-out" }}>
      <div className="rounded-xl border border-command-border bg-command-surface/80 px-4 py-3 flex items-center gap-3">
        <Loader2 className="w-4 h-4 text-command-accent animate-spin" />
        <span className="cmd-meta">PROCESSING_QUERY...</span>
      </div>
    </div>
  );
}

/* ── Empty state ── */
function EmptyState() {
  return (
    <div className="h-full flex flex-col items-center justify-center text-center px-4 select-none">
      {/* Orbit icon */}
      <div className="mb-5 relative w-16 h-16">
        <div className="absolute inset-0 rounded-full border border-command-accent/20" />
        <div className="absolute inset-2 rounded-full border border-command-accent/10" />
        <div className="absolute inset-0 flex items-center justify-center">
          <svg viewBox="0 0 24 24" fill="none" className="w-7 h-7 text-command-accent/60">
            <circle cx="12" cy="12" r="3" stroke="currentColor" strokeWidth="1.5" />
            <ellipse cx="12" cy="12" rx="10" ry="4.5" stroke="currentColor" strokeWidth="1" strokeDasharray="2 2" />
          </svg>
        </div>
      </div>
      <p className="cmd-label mb-2">SYSTEM READY</p>
      <h2 className="text-base font-semibold text-white mb-2">
        Mutual Fund FAQ Assistant
      </h2>
      <p className="text-xs text-command-muted max-w-xs leading-relaxed">
        Query fund types, taxation, guidelines, expense ratios, SIP minimums, and other
        factual mutual fund information.
      </p>
    </div>
  );
}

/* ── Main export ── */
export function MessageList({ messages, isLoading }: MessageListProps) {
  return (
    <div className="flex-1 overflow-y-auto px-4 md:px-6 py-5 space-y-5 custom-scrollbar">
      {messages.length === 0 && !isLoading ? <EmptyState /> : null}

      {messages.map((message) => (
        <div
          key={message.id}
          className={`flex ${message.type === "user" ? "justify-end" : "justify-start"}`}
        >
          {message.type === "user" ? (
            <UserMessage message={message} />
          ) : (
            <AssistantMessage message={message} />
          )}
        </div>
      ))}

      {isLoading ? (
        <div className="flex justify-start">
          <LoadingIndicator />
        </div>
      ) : null}
    </div>
  );
}
