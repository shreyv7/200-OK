import { calculateAlignmentAt } from "@/lib/trellis/gapScore";
import type { BottleneckView } from "@/lib/trellis/store";
import type { DeclaredSelf, EvidenceEvent } from "@/lib/trellis/types";

export type BottleneckDayStatus = "exists" | "still" | "overcome" | "clear";

export interface BottleneckTimelineDay {
  key: string;
  label: string;
  date: Date;
}

export interface BottleneckTimelineRow {
  id: string;
  name: string;
  statuses: BottleneckDayStatus[];
}

export interface BottleneckSparkPoint {
  day: number;
  label: string;
  declared: number;
  revealed: number;
}

export interface BottleneckTimelineModel {
  days: BottleneckTimelineDay[];
  rows: BottleneckTimelineRow[];
  spark: BottleneckSparkPoint[];
}

const WINDOW_DAYS = 5;
const CREATE_KINDS = new Set(["creation", "completion", "real_world"]);

interface DayBucket {
  key: string;
  label: string;
  date: Date;
  driftCount: number;
  createCount: number;
  passiveCount: number;
  isActive: boolean;
  isHealthy: boolean;
}

function startOfDay(date: Date): Date {
  const d = new Date(date);
  d.setHours(0, 0, 0, 0);
  return d;
}

function endOfDay(date: Date): Date {
  const d = new Date(date);
  d.setHours(23, 59, 59, 999);
  return d;
}

function weekdayLabel(date: Date): string {
  return date.toLocaleDateString(undefined, { weekday: "short" });
}

function buildDayBuckets(events: EvidenceEvent[], now: Date | string): DayBucket[] {
  const nowMs = new Date(now).getTime();
  const buckets: DayBucket[] = [];

  for (let offset = WINDOW_DAYS - 1; offset >= 0; offset -= 1) {
    const date = startOfDay(new Date(nowMs - offset * 86_400_000));
    const dayStart = startOfDay(date);
    const dayEnd = endOfDay(date);

    const dayEvents = events.filter((event) => {
      const at = new Date(event.occurredAt);
      return at >= dayStart && at <= dayEnd;
    });

    const driftCount = dayEvents.filter((e) => e.kind === "drift" || e.kind === "dismissal").length;
    const createCount = dayEvents.filter((e) => CREATE_KINDS.has(e.kind)).length;
    const passiveCount = dayEvents.filter((e) => e.kind === "passive_learning").length;

    const isHealthy = createCount > 0;
    const isActive =
      (driftCount > 0 && createCount === 0) ||
      (createCount === 0 && passiveCount >= 2) ||
      (createCount === 0 && driftCount === 0 && passiveCount === 0 && offset > 0);

    buckets.push({
      key: dayStart.toISOString().slice(0, 10),
      label: weekdayLabel(date),
      date,
      driftCount,
      createCount,
      passiveCount,
      isActive,
      isHealthy,
    });
  }

  return buckets;
}

function deriveStatuses(buckets: DayBucket[]): BottleneckDayStatus[] {
  const statuses: BottleneckDayStatus[] = buckets.map(() => "clear");
  let inActiveStreak = false;
  let seenOvercome = false;

  for (let i = 0; i < buckets.length; i += 1) {
    const bucket = buckets[i]!;

    if (!seenOvercome && bucket.isHealthy && inActiveStreak) {
      statuses[i] = "overcome";
      seenOvercome = true;
      inActiveStreak = false;
      continue;
    }

    if (seenOvercome) {
      statuses[i] = "clear";
      continue;
    }

    if (bucket.isActive) {
      statuses[i] = inActiveStreak ? "still" : "exists";
      inActiveStreak = true;
      continue;
    }

    if (inActiveStreak) {
      statuses[i] = "still";
    }
  }

  if (statuses.every((status) => status === "clear")) {
    statuses[0] = "exists";
    for (let i = 1; i < buckets.length - 1; i += 1) {
      statuses[i] = "still";
    }
    const last = buckets[buckets.length - 1]!;
    statuses[buckets.length - 1] = last.isHealthy ? "overcome" : "still";
  }

  return statuses;
}

function deriveSecondaryStatuses(buckets: DayBucket[]): BottleneckDayStatus[] {
  const statuses: BottleneckDayStatus[] = buckets.map(() => "clear");
  let inActiveStreak = false;

  for (let i = 0; i < buckets.length; i += 1) {
    const bucket = buckets[i]!;
    const friction = bucket.passiveCount >= 2 && bucket.createCount === 0;

    if (friction) {
      statuses[i] = inActiveStreak ? "still" : "exists";
      inActiveStreak = true;
      continue;
    }

    if (inActiveStreak && bucket.createCount > 0) {
      statuses[i] = "overcome";
      inActiveStreak = false;
      continue;
    }

    if (inActiveStreak) {
      statuses[i] = "still";
    }
  }

  return statuses;
}

function hasSecondarySignal(statuses: BottleneckDayStatus[]): boolean {
  return statuses.some((status) => status !== "clear");
}

function buildSpark(
  events: EvidenceEvent[],
  declaredSelf: DeclaredSelf,
  now: Date | string,
  days: BottleneckTimelineDay[],
): BottleneckSparkPoint[] {
  const nowMs = new Date(now).getTime();

  return days.map((day, index) => {
    const at = endOfDay(day.date);
    const pastEvents = events.filter((event) => new Date(event.occurredAt) <= at);
    const alignment = calculateAlignmentAt(pastEvents, declaredSelf, at).alignment;

    return {
      day: index,
      label: day.label,
      declared: Math.round(40 + index * 12.5),
      revealed: alignment,
    };
  });
}

export function buildBottleneckTimeline(input: {
  events: EvidenceEvent[];
  bottleneck: BottleneckView;
  declaredSelf: DeclaredSelf;
  now: Date | string;
  personaBottleneckLabel?: string;
}): BottleneckTimelineModel {
  const buckets = buildDayBuckets(input.events, input.now);
  const days: BottleneckTimelineDay[] = buckets.map(({ key, label, date }) => ({
    key,
    label,
    date,
  }));

  const primaryStatuses = deriveStatuses(buckets);
  const rows: BottleneckTimelineRow[] = [
    {
      id: "primary",
      name: input.bottleneck.name,
      statuses: primaryStatuses,
    },
  ];

  const secondaryName = input.personaBottleneckLabel?.trim();
  const primaryNorm = input.bottleneck.name.trim().toLowerCase();
  if (secondaryName && secondaryName.toLowerCase() !== primaryNorm) {
    const secondaryStatuses = deriveSecondaryStatuses(buckets);
    if (hasSecondarySignal(secondaryStatuses)) {
      rows.push({
        id: "secondary",
        name: secondaryName,
        statuses: secondaryStatuses,
      });
    }
  }

  const spark = buildSpark(input.events, input.declaredSelf, input.now, days);

  return { days, rows, spark };
}

export const BOTTLENECK_STATUS_COPY: Record<
  BottleneckDayStatus,
  { short: string; tone: "muted" | "signal" | "growth" | "quiet" }
> = {
  exists: { short: "It exists", tone: "signal" },
  still: { short: "Still there", tone: "muted" },
  overcome: { short: "Overcome!", tone: "growth" },
  clear: { short: "Clear", tone: "quiet" },
};
