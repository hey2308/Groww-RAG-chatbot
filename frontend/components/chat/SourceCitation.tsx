import { ExternalLink } from "lucide-react";

interface SourceCitationProps {
  source: string;
  variant?: "default" | "compliance";
}

function formatSourceLabel(source: string): string {
  try {
    const url = new URL(source);
    const host = url.hostname.replace(/^www\./, "").toUpperCase();
    const path = url.pathname.replace(/^\//, "").replace(/\//g, "_").toUpperCase();
    return path ? `SRC://${host}_${path}` : `SRC://${host}`;
  } catch {
    return "SRC://OFFICIAL_AMFI_GUIDELINES";
  }
}

export function SourceCitation({ source, variant = "default" }: SourceCitationProps) {
  const label = formatSourceLabel(source);

  if (variant === "compliance") {
    return (
      <a
        href={source}
        target="_blank"
        rel="noopener noreferrer"
        className="source-link group"
      >
        <span>EXECUTE: ACCESS_AMFI_EDUCATIONAL_DB</span>
        <span className="group-hover:translate-x-0.5 transition-transform inline-block">→</span>
      </a>
    );
  }

  return (
    <a
      href={source}
      target="_blank"
      rel="noopener noreferrer"
      className="source-link"
    >
      <ExternalLink className="w-3 h-3 shrink-0" />
      <span>{label}</span>
    </a>
  );
}
