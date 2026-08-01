export function reportLovableError(error: Error, context?: Record<string, unknown>): void {
  console.error("Reported Error:", error, context);
}
