import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import type { ApiMeUser } from "@/lib/api/types";

export type AuthSessionStatus =
  | "bootstrapping"
  | "signed_out"
  | "provisioning"
  | "ready"
  | "error";

export interface PlatformUser {
  id: string;
  clerkId?: string | null;
  email?: string | null;
  fullName?: string | null;
  profileImage?: string | null;
}

interface AuthSessionContextValue {
  status: AuthSessionStatus;
  user: PlatformUser | null;
  error: string | null;
  setBootstrapping: () => void;
  setSignedOut: () => void;
  setProvisioning: () => void;
  setReady: (user: PlatformUser) => void;
  setError: (message: string) => void;
}

const AuthSessionContext = createContext<AuthSessionContextValue | null>(null);

export function mapMeToPlatformUser(me: ApiMeUser): PlatformUser {
  return {
    id: me.id,
    clerkId: me.clerkId ?? null,
    email: me.email ?? null,
    fullName: me.fullName ?? null,
    profileImage: me.profileImage ?? null,
  };
}

export function AuthSessionProvider({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<AuthSessionStatus>("bootstrapping");
  const [user, setUser] = useState<PlatformUser | null>(null);
  const [error, setErrorState] = useState<string | null>(null);

  const setBootstrapping = useCallback(() => {
    setStatus("bootstrapping");
    setErrorState(null);
  }, []);

  const setSignedOut = useCallback(() => {
    setUser(null);
    setErrorState(null);
    setStatus("signed_out");
  }, []);

  const setProvisioning = useCallback(() => {
    setStatus("provisioning");
    setErrorState(null);
  }, []);

  const setReady = useCallback((next: PlatformUser) => {
    setUser(next);
    setErrorState(null);
    setStatus("ready");
  }, []);

  const setError = useCallback((message: string) => {
    setErrorState(message);
    setStatus("error");
  }, []);

  const value = useMemo(
    () => ({
      status,
      user,
      error,
      setBootstrapping,
      setSignedOut,
      setProvisioning,
      setReady,
      setError,
    }),
    [
      status,
      user,
      error,
      setBootstrapping,
      setSignedOut,
      setProvisioning,
      setReady,
      setError,
    ],
  );

  return (
    <AuthSessionContext.Provider value={value}>{children}</AuthSessionContext.Provider>
  );
}

export function useAuthSession(): AuthSessionContextValue {
  const ctx = useContext(AuthSessionContext);
  if (!ctx) {
    throw new Error("useAuthSession must be used within AuthSessionProvider");
  }
  return ctx;
}
