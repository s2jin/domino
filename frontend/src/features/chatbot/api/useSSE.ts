import { useCallback, useRef, useState } from "react";
import { endpoint } from "@services/config/endpoints.config";
import { type SSEEvent } from "../types";

interface SessionStreamState {
  doingMessages: string[];
  streamingContent: string;
  doneMessage: string | null;
  isStreaming: boolean;
  pendingUserMessage: string | null;
}

const defaultState: SessionStreamState = {
  doingMessages: [],
  streamingContent: "",
  doneMessage: null,
  isStreaming: false,
  pendingUserMessage: null,
};

export const useSSE = () => {
  const [sessions, setSessions] = useState<Record<number, SessionStreamState>>({});
  const abortRefs = useRef<Record<number, AbortController>>({});

  const getSessionState = useCallback(
    (sessionId: number | null): SessionStreamState => {
      if (sessionId === null) return defaultState;
      return sessions[sessionId] ?? defaultState;
    },
    [sessions],
  );

  const updateSession = useCallback(
    (sessionId: number, update: Partial<SessionStreamState>) => {
      setSessions((prev) => ({
        ...prev,
        [sessionId]: { ...(prev[sessionId] ?? defaultState), ...update },
      }));
    },
    [],
  );

  const startStream = useCallback(
    (
      sessionId: number,
      pendingMessage: string,
      onConnected: () => void,
      onDone: (content: string) => void,
    ) => {
      const token = localStorage.getItem("auth_token");
      const abortController = new AbortController();
      abortRefs.current[sessionId] = abortController;

      updateSession(sessionId, {
        isStreaming: true,
        doingMessages: [],
        streamingContent: "",
        doneMessage: null,
        pendingUserMessage: pendingMessage,
      });

      const base = endpoint.endsWith("/") ? endpoint : `${endpoint}/`;
      const url = `${base}chatbot/sessions/${sessionId}/stream`;

      fetch(url, {
        headers: { Authorization: `Bearer ${token}` },
        signal: abortController.signal,
      })
        .then(async (response) => {
          if (!response.ok || !response.body) {
            updateSession(sessionId, { isStreaming: false, pendingUserMessage: null });
            return;
          }

          const reader = response.body.getReader();
          const decoder = new TextDecoder();
          let buffer = "";

          while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split("\n");
            buffer = lines.pop() ?? "";

            for (const line of lines) {
              if (!line.startsWith("data: ")) continue;
              try {
                const event: SSEEvent = JSON.parse(line.slice(6));
                if (event.type === "ping") continue;
                if (event.type === ("connected" as string)) {
                  onConnected();
                } else if (event.type === "doing" || event.type === ("tool" as string)) {
                  const label = event.type === ("tool" as string) ? `🔧 ${event.content}` : event.content;
                  setSessions((prev) => {
                    const s = prev[sessionId] ?? defaultState;
                    return {
                      ...prev,
                      [sessionId]: {
                        ...s,
                        streamingContent: label,
                        doingMessages: [...s.doingMessages, label],
                      },
                    };
                  });
                } else if (event.type === "done") {
                  updateSession(sessionId, {
                    streamingContent: "",
                    doneMessage: event.content,
                    isStreaming: false,
                  });
                  onDone(event.content);
                  return;
                } else if (event.type === "cancelled" || event.type === "error") {
                  updateSession(sessionId, {
                    streamingContent: "",
                    isStreaming: false,
                    pendingUserMessage: null,
                  });
                  return;
                }
              } catch {
                // ignore
              }
            }
          }
          updateSession(sessionId, { isStreaming: false });
        })
        .catch(() => {
          updateSession(sessionId, {
            isStreaming: false,
            streamingContent: "",
            pendingUserMessage: null,
          });
        });
    },
    [updateSession],
  );

  const stopStream = useCallback((sessionId: number) => {
    if (abortRefs.current[sessionId]) {
      abortRefs.current[sessionId].abort();
      delete abortRefs.current[sessionId];
    }
    setSessions((prev) => ({
      ...prev,
      [sessionId]: {
        ...(prev[sessionId] ?? defaultState),
        isStreaming: false,
        streamingContent: "",
      },
    }));
  }, []);

  const clearDoneMessage = useCallback((sessionId: number) => {
    setSessions((prev) => ({
      ...prev,
      [sessionId]: {
        ...(prev[sessionId] ?? defaultState),
        doneMessage: null,
        pendingUserMessage: null,
      },
    }));
  }, []);

  return {
    startStream,
    stopStream,
    getSessionState,
    clearDoneMessage,
  };
};
