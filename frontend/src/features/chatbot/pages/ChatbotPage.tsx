import { Box, useTheme } from "@mui/material";
import React, { useCallback, useState } from "react";
import { ChatSidebar } from "../components/ChatSidebar";
import { ChatWindow } from "../components/ChatWindow";
import {
  useChatSessions,
  useCreateSession,
  useDeleteSession,
} from "../api/useChat";
import { useSSE } from "../api/useSSE";
import { type ChatSession } from "../types";

export const ChatbotPage: React.FC = () => {
  const theme = useTheme();
  const [activeSessionId, setActiveSessionId] = useState<number | null>(null);

  const { data: sessions = [] } = useChatSessions();
  const createSession = useCreateSession();
  const deleteSession = useDeleteSession();
  const sseHook = useSSE();

  const handleCreateSession = useCallback(() => {
    createSession.mutate(undefined, {
      onSuccess: (data: unknown) => {
        const session = data as ChatSession;
        setActiveSessionId(session.id);
      },
    });
  }, [createSession]);

  const handleDeleteSession = useCallback(
    (id: number) => {
      deleteSession.mutate(id, {
        onSuccess: () => {
          if (activeSessionId === id) {
            setActiveSessionId(null);
          }
        },
      });
    },
    [deleteSession, activeSessionId],
  );

  return (
    <Box
      sx={{
        display: "flex",
        height: "calc(100vh - 100px)",
        border: `1px solid ${theme.palette.divider}`,
        borderRadius: 2,
        overflow: "hidden",
        bgcolor: theme.palette.background.paper,
      }}
    >
      <ChatSidebar
        sessions={sessions}
        activeSessionId={activeSessionId}
        onSelectSession={setActiveSessionId}
        onCreateSession={handleCreateSession}
        onDeleteSession={handleDeleteSession}
      />
      <ChatWindow sessionId={activeSessionId} sseHook={sseHook} />
    </Box>
  );
};
