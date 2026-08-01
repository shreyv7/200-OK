export function renderErrorPage(error: any): string {
  return `<!DOCTYPE html><html><head><title>Error</title></head><body><h1>An error occurred</h1><pre>${error?.message || String(error)}</pre></body></html>`;
}
