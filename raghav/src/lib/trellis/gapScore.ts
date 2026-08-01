export function calculateGapScore(
  createRatio: number,
  consumeRatio: number,
  driftRatio: number
): number {
  const score = createRatio * 100 - driftRatio * 50;
  return Math.max(0, Math.min(100, Math.round(score)));
}
