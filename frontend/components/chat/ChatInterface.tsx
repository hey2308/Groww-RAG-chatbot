"use client";

import { useMutation } from "@tanstack/react-query";
import axios, { AxiosError } from "axios";
import { useEffect, useState } from "react";

import { ChatResponse, Message } from "../types";
import { detectMessageVariant } from "./messageUtils";
import { InputArea } from "./InputArea";
import { MessageList } from "./MessageList";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface ChatInterfaceProps {
  messages: Message[];
  onAppendMessage: (message: Message) => void;
  presetQuestion?: string | null;
  onPresetConsumed?: () => void;
}

export function ChatInterface({
  messages,
  onAppendMessage,
  presetQuestion,
  onPresetConsumed,
}: ChatInterfaceProps) {
  const [input, setInput] = useState("");

  const mutation = useMutation({
    mutationFn: async (query: string) => {
      const response = await axios.post<ChatResponse>(`${API_URL}/api/chat`, { query });
      return response.data;
    },
    onSuccess: (data) => {
      const assistantMessage: Message = {
        id: crypto.randomUUID(),
        type: "assistant",
        content: data.response,
        source: data.source ?? undefined,
        timestamp: new Date(data.timestamp),
        variant: detectMessageVariant(data.response),
      };
      onAppendMessage(assistantMessage);
    },
    onError: (error: AxiosError<{ detail?: string }>) => {
      const detail =
        error.response?.data?.detail || "Sorry, I encountered an error. Please try again later.";
      const assistantMessage: Message = {
        id: crypto.randomUUID(),
        type: "assistant",
        content: detail,
        timestamp: new Date(),
        variant: "error",
      };
      onAppendMessage(assistantMessage);
    },
  });

  const isLoading = mutation.isPending;

  const sendMessage = (query: string) => {
    if (!query.trim() || isLoading) return;
    const userMessage: Message = {
      id: crypto.randomUUID(),
      type: "user",
      content: query.trim(),
      timestamp: new Date(),
    };
    onAppendMessage(userMessage);
    mutation.mutate(query.trim());
  };

  const handleSubmit = () => {
    if (!input.trim() || isLoading) return;
    const query = input.trim();
    setInput("");
    sendMessage(query);
  };

  useEffect(() => {
    if (!presetQuestion || isLoading) return;
    sendMessage(presetQuestion);
    onPresetConsumed?.();
    setInput("");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [presetQuestion]);

  return (
    <section className="flex-1 overflow-hidden flex flex-col min-h-0">
      <MessageList messages={messages} isLoading={isLoading} />
      <InputArea input={input} isLoading={isLoading} onInputChange={setInput} onSubmit={handleSubmit} />
    </section>
  );
}
