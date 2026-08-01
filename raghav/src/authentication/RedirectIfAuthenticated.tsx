import { useAuth } from "@clerk/react";
import { useNavigate, useSearch } from "@tanstack/react-router";
import { useEffect, type ReactNode } from "react";

import { AuthLoading } from "./AuthLoading";

export function RedirectIfAuthenticated({
  children,
  fallback = "/dashboard",
}: {
  children: ReactNode;
  fallback?: string;
}) {
  const { isLoaded, isSignedIn } = useAuth();
  const navigate = useNavigate();
  const search = useSearch({ strict: false }) as { redirect?: string };

  useEffect(() => {
    if (!isLoaded || !isSignedIn) return;
    const target =
      search.redirect && search.redirect.startsWith("/") ? search.redirect : fallback;
    void navigate({ to: target, replace: true });
  }, [fallback, isLoaded, isSignedIn, navigate, search.redirect]);

  if (!isLoaded) {
    return <AuthLoading label="Loading…" />;
  }

  if (isSignedIn) {
    return <AuthLoading label="Redirecting…" />;
  }

  return <>{children}</>;
}
