import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

const API_BASE =
  import.meta.env.VITE_API_BASE ?? "http://localhost:8002/api/v1";

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
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/integrations/status`);
      if (!res.ok) {
        throw new Error("Failed to fetch integrations status");
      }
      return res.json();
    },
    staleTime: 10000,
  });
}

export function useConnectProvider() {
  return useMutation<ConnectResponse, Error, string>({
    mutationFn: async (provider: string) => {
      const res = await fetch(`${API_BASE}/integrations/${provider}/connect`);
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Failed to generate auth URL for ${provider}`);
      }
      return res.json();
    },
  });
}

export function useRevokeProvider() {
  const queryClient = useQueryClient();
  return useMutation<{ provider: string; disconnected: boolean }, Error, string>({
    mutationFn: async (provider: string) => {
      const res = await fetch(`${API_BASE}/integrations/${provider}`, {
        method: "DELETE",
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Failed to revoke ${provider} integration`);
      }
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["integrations-status"] });
    },
  });
}

export function useTriggerGithubSync() {
  const queryClient = useQueryClient();
  return useMutation<GithubSyncResponse, Error, void>({
    mutationFn: async () => {
      const res = await fetch(`${API_BASE}/github/sync`, {
        method: "POST",
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Failed to trigger GitHub sync");
      }
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["integrations-status"] });
    },
  });
}
