import {
  Box,
  TextField,
  IconButton,
  Typography,
  CircularProgress,
  useTheme,
} from "@mui/material";
import {
  Send as SendIcon,
  Stop as StopIcon,
} from "@mui/icons-material";
import React, { useCallback, useEffect, useMemo, useRef } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { ChatMessageBubble } from "./ChatMessage";
import { ThinkBlock } from "./ThinkBlock";
import { useChatSessionDetail, useSendMessage, useCancelSession } from "../api/useChat";
import { useSSE } from "../api/useSSE";
import { type ChatMessage } from "../types";

interface ChatWindowProps {
  sessionId: number | null;
  sseHook: ReturnType<typeof useSSE>;
}

type RenderItem =
  | { type: "message"; msg: ChatMessage }
  | { type: "think"; steps: string[] };

export const ChatWindow: React.FC<ChatWindowProps> = ({ sessionId, sseHook }) => {
  const theme = useTheme();
  const [input, setInput] = React.useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const queryClient = useQueryClient();

  const { data: session, isLoading } = useChatSessionDetail(sessionId);
  const sendMessage = useSendMessage();
  const cancelSession = useCancelSession();

  const { startStream, stopStream, getSessionState, clearDoneMessage } = sseHook;
  const state = getSessionState(sessionId);
  const { isStreaming, streamingContent, doneMessage, pendingUserMessage } = state;

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  // Group DB messages: consecutive think messages become a ThinkBlock
  const renderItems: RenderItem[] = useMemo(() => {
    if (!session?.messages) return [];
    const items: RenderItem[] = [];
    let thinkGroup: string[] = [];

    for (const msg of session.messages) {
      if (msg.role === "think") {
        thinkGroup.push(msg.content);
      } else {
        if (thinkGroup.length > 0) {
          items.push({ type: "think", steps: thinkGroup });
          thinkGroup = [];
        }
        items.push({ type: "message", msg });
      }
    }
    if (thinkGroup.length > 0) {
      items.push({ type: "think", steps: thinkGroup });
    }
    return items;
  }, [session?.messages]);

  useEffect(() => {
    scrollToBottom();
  }, [renderItems, streamingContent, pendingUserMessage, doneMessage, scrollToBottom]);

  // When session data refreshes after done, clear temporary states
  useEffect(() => {
    if (sessionId && doneMessage && session?.messages) {
      const lastMsg = session.messages[session.messages.length - 1];
      if (lastMsg && lastMsg.role === "assistant" && lastMsg.content === doneMessage) {
        clearDoneMessage(sessionId);
      }
    }
  }, [session?.messages, sessionId, doneMessage, clearDoneMessage]);

  const handleSend = useCallback(() => {
    if (!input.trim() || !sessionId || sendMessage.isPending || isStreaming)
      return;

    const content = input.trim();
    setInput("");

    startStream(
      sessionId,
      content,
      () => {
        sendMessage.mutate(
          { sessionId, content },
          {
            onError: () => {
              stopStream(sessionId);
            },
          },
        );
      },
      () => {
        void queryClient.invalidateQueries({
          queryKey: ["CHAT_SESSION_DETAIL", sessionId],
        });
      },
    );
  }, [input, sessionId, sendMessage, isStreaming, startStream, stopStream, queryClient]);

  const handleCancel = useCallback(() => {
    if (!sessionId) return;
    cancelSession.mutate(sessionId);
    stopStream(sessionId);
    void queryClient.invalidateQueries({
      queryKey: ["CHAT_SESSION_DETAIL", sessionId],
    });
  }, [sessionId, cancelSession, stopStream, queryClient]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        handleSend();
      }
    },
    [handleSend],
  );

  if (!sessionId) {
    return (
      <Box
        sx={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center" }}
      >
        <Typography color="text.secondary">
          Select a chat or create a new one
        </Typography>
      </Box>
    );
  }

  if (isLoading) {
    return (
      <Box
        sx={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center" }}
      >
        <CircularProgress />
      </Box>
    );
  }

  const isBusy = sendMessage.isPending || isStreaming || pendingUserMessage !== null;

  return (
    <Box sx={{ flex: 1, display: "flex", flexDirection: "column", height: "100%" }}>
      {/* Messages area */}
      <Box sx={{ flex: 1, overflow: "auto", px: 3, py: 2 }}>
        {renderItems.map((item, idx) =>
          item.type === "think" ? (
            <ThinkBlock key={`think-${idx}`} steps={item.steps} isThinking={false} />
          ) : (
            <ChatMessageBubble
              key={item.msg.id}
              role={item.msg.role as "user" | "assistant"}
              content={item.msg.content}
            />
          ),
        )}

        {/* Optimistic pending user message */}
        {pendingUserMessage && (
          <ChatMessageBubble role="user" content={pendingUserMessage} />
        )}

        {/* Live think block from SSE */}
        {pendingUserMessage && isStreaming && (
          <ThinkBlock
            steps={state.doingMessages.slice(0, -1)}
            currentStep={streamingContent || "think"}
            isThinking
          />
        )}

        {/* Done message before DB refresh */}
        {!isStreaming && doneMessage && (
          <>
            {state.doingMessages.length > 0 && (
              <ThinkBlock steps={state.doingMessages} isThinking={false} />
            )}
            <ChatMessageBubble role="assistant" content={doneMessage} />
          </>
        )}

        <div ref={messagesEndRef} />
      </Box>

      {/* Input area */}
      <Box
        sx={{
          p: 2,
          borderTop: `1px solid ${theme.palette.divider}`,
          display: "flex",
          gap: 1,
          alignItems: "flex-end",
        }}
      >
        <TextField
          fullWidth
          multiline
          maxRows={4}
          size="small"
          placeholder="Type a message..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isBusy}
        />
        {isBusy ? (
          <IconButton color="error" onClick={handleCancel}>
            <StopIcon />
          </IconButton>
        ) : (
          <IconButton
            color="primary"
            onClick={handleSend}
            disabled={!input.trim()}
          >
            <SendIcon />
          </IconButton>
        )}
      </Box>
    </Box>
  );
};
