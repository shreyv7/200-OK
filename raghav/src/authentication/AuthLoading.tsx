export function AuthLoading({ label = "Loading…" }: { label?: string }) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="text-center">
        <div className="mx-auto h-8 w-8 animate-pulse rounded-full border border-border bg-muted" />
        <p className="mt-4 font-mono text-xs tracking-[0.14em] text-muted-foreground uppercase">
          {label}
        </p>
      </div>
    </div>
  );
}
