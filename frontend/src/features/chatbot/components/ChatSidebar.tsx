import {
  Box,
  List,
  ListItemButton,
  ListItemText,
  IconButton,
  Typography,
  Button,
  Tooltip,
  useTheme,
} from "@mui/material";
import {
  Add as AddIcon,
  Delete as DeleteIcon,
} from "@mui/icons-material";
import React from "react";
import { type ChatSession } from "../types";

interface ChatSidebarProps {
  sessions: ChatSession[];
  activeSessionId: number | null;
  onSelectSession: (id: number) => void;
  onCreateSession: () => void;
  onDeleteSession: (id: number) => void;
}

export const ChatSidebar: React.FC<ChatSidebarProps> = ({
  sessions,
  activeSessionId,
  onSelectSession,
  onCreateSession,
  onDeleteSession,
}) => {
  const theme = useTheme();

  return (
    <Box
      sx={{
        width: 260,
        height: "100%",
        borderRight: `1px solid ${theme.palette.divider}`,
        display: "flex",
        flexDirection: "column",
        bgcolor:
          theme.palette.mode === "dark"
            ? theme.palette.grey[900]
            : theme.palette.grey[50],
      }}
    >
      <Box sx={{ p: 1.5 }}>
        <Button
          variant="outlined"
          startIcon={<AddIcon />}
          fullWidth
          onClick={onCreateSession}
          size="small"
        >
          New Chat
        </Button>
      </Box>
      <List sx={{ flex: 1, overflow: "auto", py: 0 }}>
        {sessions.map((s) => (
          <ListItemButton
            key={s.id}
            selected={s.id === activeSessionId}
            onClick={() => onSelectSession(s.id)}
            sx={{
              py: 1,
              px: 1.5,
              "&.Mui-selected": {
                bgcolor:
                  theme.palette.mode === "dark"
                    ? theme.palette.grey[800]
                    : theme.palette.action.selected,
              },
            }}
          >
            <ListItemText
              primary={
                <Typography variant="body2" noWrap>
                  {s.title}
                </Typography>
              }
            />
            <Tooltip title="Delete">
              <IconButton
                size="small"
                onClick={(e) => {
                  e.stopPropagation();
                  onDeleteSession(s.id);
                }}
                sx={{ ml: 0.5 }}
              >
                <DeleteIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          </ListItemButton>
        ))}
      </List>
    </Box>
  );
};
