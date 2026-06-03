import { Search, Send } from "lucide-react";
import { KeyboardEvent } from "react";

interface InputAreaProps {
  input: string;
  isLoading: boolean;
  onInputChange: (value: string) => void;
  onSubmit: () => void;
}

export function InputArea({ input, isLoading, onInputChange, onSubmit }: InputAreaProps) {
  const onKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      onSubmit();
    }
  };

  return (
    <div className="shrink-0 border-t border-command-border bg-command-panel/80 backdrop-blur-sm px-4 md:px-5 py-4">
      {/* Input row */}
      <div className="flex items-center gap-3">
        <div className="flex-1 relative">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-command-muted pointer-events-none" />
          <input
            type="text"
            value={input}
            onChange={(e) => onInputChange(e.target.value)}
            onKeyDown={onKeyDown}
            placeholder="QUERY_SYSTEM: Fund types, taxation, guidelines..."
            className="w-full pl-10 pr-4 py-3 rounded-xl bg-command-surface border border-command-border text-sm text-command-text placeholder:text-command-muted/60 focus:outline-none focus:border-command-accent/50 focus:ring-1 focus:ring-command-accent/20 transition-all font-mono disabled:opacity-50"
            disabled={isLoading}
          />
        </div>

        {/* Send button — teal circle */}
        <button
          type="button"
          onClick={onSubmit}
          disabled={isLoading || !input.trim()}
          aria-label="Send message"
          className="shrink-0 w-10 h-10 flex items-center justify-center rounded-full bg-command-accent text-command-bg hover:bg-command-accent-dim disabled:bg-command-border disabled:text-command-muted disabled:cursor-not-allowed transition-all shadow-glow-sm hover:shadow-glow disabled:shadow-none"
        >
          {isLoading ? (
            <div className="animate-spin rounded-full h-4 w-4 border-2 border-command-bg border-t-transparent" />
          ) : (
            <Send className="w-3.5 h-3.5" />
          )}
        </button>
      </div>

      {/* Footer note */}
      <p className="mt-2.5 text-center font-mono text-[9px] tracking-widest text-command-muted/70 uppercase">
        © DATA_SOURCE: OFFICIAL_AMFI_SEBI_DOCS // FACTUAL_MODE_ONLY
      </p>
    </div>
  );
}
