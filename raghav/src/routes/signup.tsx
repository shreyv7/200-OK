import { SignUp } from "@clerk/react";
import { Link, createFileRoute } from "@tanstack/react-router";

import { RedirectIfAuthenticated } from "@/authentication";
import { clerkAppearance } from "@/authentication/clerkAppearance";
import { LatticeMark } from "@/components/trellis/Lattice";

type SignupSearch = {
  redirect?: string | undefined;
};

export const Route = createFileRoute("/signup")({
  validateSearch: (search: Record<string, unknown>): SignupSearch => {
    const redirect = search["redirect"];
    return typeof redirect === "string" ? { redirect } : {};
  },
  head: () => ({
    meta: [
      { title: "Sign up — Trellis" },
      { name: "description", content: "Create your Trellis account." },
    ],
  }),
  component: SignupPage,
});

function SignupPage() {
  const { redirect } = Route.useSearch();
  const forceRedirectUrl =
    redirect && redirect.startsWith("/") ? redirect : "/onboarding";

  return (
    <RedirectIfAuthenticated fallback={forceRedirectUrl}>
      <div className="relative flex min-h-screen flex-col items-center justify-center px-4 py-12 overflow-hidden">
        <div className="relative z-10 mb-8 flex items-center gap-3">
          <LatticeMark className="h-5 w-5 text-foreground" />
          <Link
            to="/"
            className="font-mono text-xs font-semibold tracking-[0.26em] text-foreground uppercase"
          >
            TRELLIS
          </Link>
        </div>
        <div className="relative z-10">
          <SignUp
            routing="hash"
            signInUrl="/login"
            forceRedirectUrl={forceRedirectUrl}
            fallbackRedirectUrl={forceRedirectUrl}
            appearance={clerkAppearance as never}
          />
        </div>
        <p className="relative z-10 mt-6 font-mono text-[11px] text-muted-foreground">
          Already have an account?{" "}
          <Link to="/login" className="text-foreground underline underline-offset-4">
            Log in
          </Link>
        </p>
      </div>
    </RedirectIfAuthenticated>
  );
}
