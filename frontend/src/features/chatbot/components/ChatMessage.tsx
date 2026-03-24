import { Box, Typography, useTheme } from "@mui/material";
import {
  Person as PersonIcon,
  SmartToy as BotIcon,
} from "@mui/icons-material";
import React from "react";

interface ChatMessageProps {
  role: "user" | "assistant";
  content: string;
  isStreaming?: boolean;
}

export const ChatMessageBubble: React.FC<ChatMessageProps> = ({
  role,
  content,
  isStreaming = false,
}) => {
  const theme = useTheme();
  const isUser = role === "user";

  return (
    <Box
      sx={{
        display: "flex",
        gap: 1.5,
        mb: 2,
        flexDirection: isUser ? "row-reverse" : "row",
        alignItems: "flex-start",
      }}
    >
      <Box
        sx={{
          width: 32,
          height: 32,
          borderRadius: "50%",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          bgcolor: isUser
            ? theme.palette.primary.main
            : theme.palette.grey[600],
          color: "#fff",
          flexShrink: 0,
        }}
      >
        {isUser ? (
          <PersonIcon sx={{ fontSize: 18 }} />
        ) : (
          <BotIcon sx={{ fontSize: 18 }} />
        )}
      </Box>
      <Box
        sx={{
          maxWidth: "70%",
          bgcolor: isUser
            ? theme.palette.primary.main
            : theme.palette.mode === "dark"
              ? theme.palette.grey[800]
              : theme.palette.grey[100],
          color: isUser
            ? "#fff"
            : theme.palette.text.primary,
          borderRadius: 2,
          px: 2,
          py: 1.5,
          position: "relative",
        }}
      >
        <Typography
          variant="body2"
          sx={{
            whiteSpace: "pre-wrap",
            wordBreak: "break-word",
            opacity: isStreaming ? 0.7 : 1,
          }}
        >
          {content}
          {isStreaming && (
            <Box
              component="span"
              sx={{
                display: "inline-block",
                width: 6,
                height: 14,
                bgcolor: "currentColor",
                ml: 0.5,
                animation: "blink 1s step-end infinite",
                "@keyframes blink": {
                  "0%, 100%": { opacity: 1 },
                  "50%": { opacity: 0 },
                },
              }}
            />
          )}
        </Typography>
      </Box>
    </Box>
  );
};
