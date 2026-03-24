export interface ChatSession {
  id: number;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface ChatMessage {
  id: number;
  session_id: number;
  role: "user" | "assistant" | "think" | "tool";
  content: string;
  created_at: string;
}

export interface ChatSessionDetail extends ChatSession {
  messages: ChatMessage[];
}

export interface SSEEvent {
  type: "doing" | "done" | "cancelled" | "error" | "ping";
  content: string;
}
