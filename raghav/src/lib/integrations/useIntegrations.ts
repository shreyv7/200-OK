import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiFetch } from "@/lib/api/client";

export interface IntegrationStatus {
  provider: string;
  connectedAt: string;
  expiresAt: string | null;
  revokedAt: string | null;
  isActive: boolean;
  scopes: string[];
}

export interface ConnectResponse {
  authUrl: string;
}

export interface GithubSyncResponse {
  provider: string;
  synced: number;
  message: string;
}

export function useIntegrationsStatus() {
  return useQuery<IntegrationStatus[]>({
    queryKey: ["integrations-status"],
    queryFn: () => apiFetch<IntegrationStatus[]>("/integrations/status"),
    staleTime: 10000,
  });
}

export function useConnectProvider() {
  return useMutation<ConnectResponse, Error, string>({
    mutationFn: (provider: string) =>
      apiFetch<ConnectResponse>(`/integrations/${provider}/connect`),
  });
}

export function useRevokeProvider() {
  const queryClient = useQueryClient();
  return useMutation<{ provider: string; disconnected: boolean }, Error, string>({
    mutationFn: async (provider: string) => {
      await apiFetch<null>(`/integrations/${provider}`, {
        method: "DELETE",
      });
      return { provider, disconnected: true };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["integrations-status"] });
    },
  });
}

export function useTriggerGithubSync() {
  const queryClient = useQueryClient();
  return useMutation<GithubSyncResponse, Error, void>({
    mutationFn: () =>
      apiFetch<GithubSyncResponse>("/github/sync", {
        method: "POST",
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["integrations-status"] });
    },
  });
}

export function useTriggerNotionSync() {
  const queryClient = useQueryClient();
  return useMutation<GithubSyncResponse, Error, void>({
    mutationFn: () =>
      apiFetch<GithubSyncResponse>("/notion/sync", {
        method: "POST",
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["integrations-status"] });
    },
  });
}

export function useTriggerCalendarSync() {
  const queryClient = useQueryClient();
  return useMutation<GithubSyncResponse, Error, void>({
    mutationFn: () =>
      apiFetch<GithubSyncResponse>("/calendar/sync", {
        method: "POST",
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["integrations-status"] });
    },
  });
}
