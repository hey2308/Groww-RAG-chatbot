import React from "react";
import { MessageVariant } from "../types";

export function detectMessageVariant(content: string): MessageVariant {
  const text = content.toLowerCase();
  if (text.includes("system_error") || text.includes("sorry, i encountered an error")) {
    return "error";
  }
  if (
    text.includes("compliance") ||
    text.includes("recommend") ||
    text.includes("investment advice") ||
    text.includes("advisor") ||
    text.includes("sebi-registered")
  ) {
    return "compliance";
  }
  return "informational";
}

export function formatTimestamp(timestamp: Date | string | number): string {
  const date = new Date(timestamp);
  if (isNaN(date.getTime())) return "12.05.2024";
  const day = String(date.getDate()).padStart(2, "0");
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const year = date.getFullYear();
  return `${day}.${month}.${year}`;
}

export function highlightFacts(content: string): React.ReactNode[] | string {
  const keywords = [
    "lock-in period of 3 years",
    "3 years",
    "Section 80C",
    "ELSS",
    "lock-in"
  ];

  // Sort by length descending to prevent shorter matches taking precedence
  const sortedKeywords = [...keywords].sort((a, b) => b.length - a.length);
  const pattern = new RegExp(`(${sortedKeywords.map(k => k.replace(/[-\/\\^$*+?.()|[\]{}]/g, '\\$&')).join('|')})`, "gi");

  const parts = content.split(pattern);
  if (parts.length === 1) return content;

  return parts.map((part, i) => {
    const isKeyword = keywords.some(k => k.toLowerCase() === part.toLowerCase());
    if (isKeyword) {
      return React.createElement(
        "span",
        { key: i, className: "text-command-accent font-medium" },
        part
      );
    }
    return part;
  });
}

export function splitResponseContent(content: string): { body: string; footer?: string } {
  const marker = "\n\nLast updated:";
  const index = content.indexOf(marker);
  if (index !== -1) {
    return {
      body: content.substring(0, index),
      footer: content.substring(index + marker.length).trim(),
    };
  }
  return { body: content };
}
