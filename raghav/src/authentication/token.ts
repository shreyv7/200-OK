type TokenGetter = () => Promise<string | null>;

let tokenGetter: TokenGetter | null = null;
let bridgeReady = false;
const readyWaiters = new Set<() => void>();

function notifyReady() {
  for (const resolve of [...readyWaiters]) {
    resolve();
  }
  readyWaiters.clear();
}

export function setAuthTokenGetter(getter: TokenGetter | null) {
  tokenGetter = getter;
  bridgeReady = true;
  notifyReady();
}

export function resetAuthBridge() {
  tokenGetter = null;
  bridgeReady = false;
}

export async function getAuthToken(): Promise<string | null> {
  const getter = tokenGetter;
  if (!getter) return null;
  return getter();
}

/** Wait for ClerkAuthBridge to finish initializing, then return a JWT (or null if signed out). */
export async function waitForAuthToken(timeoutMs = 8000): Promise<string | null> {
  const immediate = tokenGetter;
  if (immediate) {
    return immediate();
  }

  if (bridgeReady) {
    return null;
  }

  await new Promise<void>((resolve) => {
    const timer = window.setTimeout(() => {
      readyWaiters.delete(onReady);
      resolve();
    }, timeoutMs);

    const onReady = () => {
      window.clearTimeout(timer);
      readyWaiters.delete(onReady);
      resolve();
    };
    readyWaiters.add(onReady);
  });

  const getter = tokenGetter;
  if (!getter) return null;
  return getter();
}
