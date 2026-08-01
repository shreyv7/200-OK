export const MIN_LOW_VALUE_RATIO = 0.3;
export const MIN_SCROLL_COUNT = 5;

/** Scrolls older than this drop out of the evaluation window. */
const WINDOW_MS = 5 * 60_000;
/** After firing, the detector stays quiet for this long. */
const COOLDOWN_MS = 10 * 60_000;

export type DetectorState = "monitoring" | "armed" | "fired" | "cooldown";

export interface ScrollRecord {
  at: number;
  kind: "low_value" | "neutral";
}

export interface DetectorInputs {
  scrollCount: number;
  lowValueRatio: number;
  inFocusWindow: boolean;
}

export interface DetectorResult {
  inputs: DetectorInputs;
  fired: boolean;
  state: DetectorState;
  evaluatedInMs: number;
}

/**
 * Deterministic drift detector — no model calls, so the demo can show the
 * exact arithmetic behind an intervention.
 */
export function evaluateMomentDetector(
  scrolls: ScrollRecord[],
  now: number,
  lastFiredAt: number | null,
): DetectorResult {
  const startedAt = performance.now();

  const recent = (scrolls ?? []).filter((s) => now - s.at <= WINDOW_MS);
  const scrollCount = recent.length;
  const lowValue = recent.filter((s) => s.kind === "low_value").length;
  const lowValueRatio = scrollCount === 0 ? 0 : lowValue / scrollCount;

  // The demo feed is an owned surface, so every session counts as declared time.
  const inFocusWindow = true;

  const inCooldown = lastFiredAt !== null && now - lastFiredAt < COOLDOWN_MS;
  const thresholdsMet =
    scrollCount >= MIN_SCROLL_COUNT &&
    lowValueRatio > MIN_LOW_VALUE_RATIO &&
    inFocusWindow;

  const fired = thresholdsMet && !inCooldown;

  let state: DetectorState;
  if (inCooldown) state = "cooldown";
  else if (fired) state = "fired";
  else if (scrollCount >= MIN_SCROLL_COUNT - 2 && lowValueRatio > MIN_LOW_VALUE_RATIO)
    state = "armed";
  else state = "monitoring";

  return {
    inputs: { scrollCount, lowValueRatio, inFocusWindow },
    fired,
    state,
    evaluatedInMs: performance.now() - startedAt,
  };
}
