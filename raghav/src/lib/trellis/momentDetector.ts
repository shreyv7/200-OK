export const MIN_LOW_VALUE_RATIO = 0.3;
export const MIN_SCROLL_COUNT = 5;

export function evaluateMomentDetector(events: any[]): { detected: boolean; reason: string | null } {
  if (!events || events.length === 0) {
    return { detected: false, reason: null };
  }
  return { detected: false, reason: null };
}
