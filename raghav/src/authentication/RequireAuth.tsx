import { useAuth } from "@clerk/react";
import { useNavigate, useRouterState } from "@tanstack/react-router";
import { useEffect, type ReactNode } from "react";

import { AuthLoading } from "./AuthLoading";
import { useAuthSession } from "./AuthSession";

export function RequireAuth({ children }: { children: ReactNode }) {
  const { isLoaded, isSignedIn } = useAuth();
  const { status, error, setProvisioning } = useAuthSession();
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

  if (!isLoaded || status === "bootstrapping") {
    return <AuthLoading label="Checking session…" />;
  }

  if (!isSignedIn || status === "signed_out") {
    return <AuthLoading label="Redirecting to login…" />;
  }

  if (status === "provisioning") {
    return <AuthLoading label="Connecting your account…" />;
  }

  if (status === "error") {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background px-6">
        <div className="max-w-md space-y-4 text-center">
          <p className="font-mono text-xs uppercase tracking-[0.16em] text-muted-foreground">
            Session
          </p>
          <h1 className="text-xl font-semibold text-foreground">
            Couldn&apos;t load your account
          </h1>
          <p className="text-sm text-muted-foreground">
            {error ||
              "Trellis couldn't create or restore your Postgres session. Check that the API is running, then try again."}
          </p>
          <button
            type="button"
            onClick={() => {
              setProvisioning();
              window.location.reload();
            }}
            className="inline-flex items-center justify-center rounded-full bg-foreground px-5 py-2.5 text-sm font-semibold text-background"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
