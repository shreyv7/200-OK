import { useAuth } from "@clerk/react";
import { useNavigate, useRouterState } from "@tanstack/react-router";
import { useEffect, type ReactNode } from "react";

import { AuthLoading } from "./AuthLoading";

export function RequireAuth({ children }: { children: ReactNode }) {
  const { isLoaded, isSignedIn } = useAuth();
  const navigate = useNavigate();
  const pathname = useRouterState({ select: (s) => s.location.pathname });

  useEffect(() => {
    if (!isLoaded) return;
    if (!isSignedIn) {
      void navigate({
        to: "/login",
        search: { redirect: pathname },
        replace: true,
      });
    }
  }, [isLoaded, isSignedIn, navigate, pathname]);

  if (!isLoaded) {
    return <AuthLoading label="Checking session…" />;
  }

  if (!isSignedIn) {
    return <AuthLoading label="Redirecting to login…" />;
  }

  return <>{children}</>;
}
