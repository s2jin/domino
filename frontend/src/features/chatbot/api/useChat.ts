import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { dominoApiClient } from "@services/clients/domino.client";
import { type ChatSession, type ChatSessionDetail } from "../types";
import { toast } from "react-toastify";
import { type AxiosError } from "axios";

const SESSIONS_KEY = "CHAT_SESSIONS";
const SESSION_DETAIL_KEY = "CHAT_SESSION_DETAIL";

export const useChatSessions = () => {
  return useQuery<ChatSession[]>({
    queryKey: [SESSIONS_KEY],
    queryFn: async () => await dominoApiClient.get("/chatbot/sessions"),
    throwOnError(e) {
      const message =
        ((e as AxiosError<{ detail?: string }>).response?.data?.detail ??
          e?.message) || "Failed to load sessions";
      toast.error(message, { toastId: message });
      return false;
    },
  });
};

export const useChatSessionDetail = (sessionId: number | null) => {
  return useQuery<ChatSessionDetail>({
    queryKey: [SESSION_DETAIL_KEY, sessionId],
    queryFn: async () =>
      await dominoApiClient.get(`/chatbot/sessions/${sessionId}`),
    enabled: sessionId !== null,
    throwOnError(e) {
      const message =
        ((e as AxiosError<{ detail?: string }>).response?.data?.detail ??
          e?.message) || "Failed to load session";
      toast.error(message, { toastId: message });
      return false;
    },
  });
};

export const useCreateSession = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (title?: string) =>
      await dominoApiClient.post("/chatbot/sessions", {
        title: title || "New Chat",
      }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: [SESSIONS_KEY] });
    },
    onError: (e: AxiosError<{ detail?: string }>) => {
      toast.error(e.response?.data?.detail ?? "Failed to create session");
    },
  });
};

export const useDeleteSession = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (sessionId: number) =>
      await dominoApiClient.delete(`/chatbot/sessions/${sessionId}`),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: [SESSIONS_KEY] });
    },
    onError: (e: AxiosError<{ detail?: string }>) => {
      toast.error(e.response?.data?.detail ?? "Failed to delete session");
    },
  });
};

export const useUpdateSessionTitle = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ sessionId, title }: { sessionId: number; title: string }) =>
      await dominoApiClient.patch(`/chatbot/sessions/${sessionId}`, { title }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: [SESSIONS_KEY] });
    },
  });
};

export const useSendMessage = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      sessionId,
      content,
    }: {
      sessionId: number;
      content: string;
    }) =>
      await dominoApiClient.post(`/chatbot/sessions/${sessionId}/messages`, {
        content,
      }),
    onSuccess: () => {
      // Don't invalidate session detail here - SSE done event handles it.
      // Only refresh session list (for title updates etc.)
      void queryClient.invalidateQueries({ queryKey: [SESSIONS_KEY] });
    },
    onError: (e: AxiosError<{ detail?: string }>) => {
      toast.error(e.response?.data?.detail ?? "Failed to send message");
    },
  });
};

export const useCancelSession = () => {
  return useMutation({
    mutationFn: async (sessionId: number) =>
      await dominoApiClient.post(`/chatbot/sessions/${sessionId}/cancel`),
  });
};
