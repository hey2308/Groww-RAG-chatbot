export type MessageVariant = "informational" | "compliance" | "error";

export interface Message {
  id: string;
  type: "user" | "assistant";
  content: string;
  source?: string;
  timestamp: Date;
  variant?: MessageVariant;
}

export interface ChatResponse {
  response: string;
  source?: string | null;
  timestamp: string;
}

export interface ChatState {
  messages: Message[];
  isLoading: boolean;
  error: string | null;
}
