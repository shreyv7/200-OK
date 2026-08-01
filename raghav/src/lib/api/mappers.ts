import type {
  ApiBottleneckPacket,
  ApiDashboardSummary,
  ApiDeclaredSelf,
  ApiGapBreakdown,
  ApiIdentityStack,
  ApiLedgerEntry,
  ApiStackElement,
  ApiStackVariants,
} from "./types";
import type {
  DeclaredSelf,
  Gap,
  LedgerEntry,
  StackElement,
  StackVariant,
  Unlearning,
} from "@/lib/trellis/types";

export interface OnboardingDeclaredView {
  headline: string;
  attributes: Array<{
    id: string;
    label: string;
    weight: number;
    markers: Array<{ id: string; label: string }>;
  }>;
}

export function mapDeclaredSelf(self: ApiDeclaredSelf): OnboardingDeclaredView {
  const headline =
    self.attributes.map((a) => a.label).join(" · ") || "Declared Self";
  return {
    headline,
    attributes: self.attributes.map((a) => ({
      id: a.id,
      label: a.label,
      weight: a.weight,
      markers: a.markers.map((m) => ({ id: m.id, label: m.label })),
    })),
  };
}

export function mapDeclaredSelfToUi(self: ApiDeclaredSelf): DeclaredSelf {
  const primary = self.attributes[0];
  return {
    id: self.id,
    name: primary?.label ?? "Declared Self",
    role: self.attributes.map((a) => a.label).join(" · ") || "Builder",
    attributes: self.attributes.map((a) => ({
      id: a.id,
      label: a.label,
      target: Math.min(1, a.targetWeeklyPoints / 15),
    })),
  };
}

export function mapGap(gap: ApiGapBreakdown, labels: Record<string, string> = {}): Gap {
  const total =
    Math.max(0.01, gap.createPoints + gap.consumePoints + gap.driftPoints);
  return {
    score: Math.round(gap.gapScore),
    alignment: Math.round(gap.alignmentScore),
    createRatio: gap.createPoints / total,
    consumeRatio: gap.consumePoints / total,
    driftRatio: gap.driftPoints / total,
    breakdown: gap.attributes.map((attr) => ({
      attributeId: attr.attributeId,
      label: labels[attr.attributeId] ?? attr.attributeId,
      weight: attr.w_i,
      target: attr.D_i,
      revealed: attr.R_i,
      deficit: attr.deficit_i,
      contribution: attr.w_i * attr.deficit_i,
      markerEvidence: [],
    })),
  };
}

function elementTypeLabel(type: string): string {
  if (type === "micro_mission") return "Micro Mission";
  if (type === "growth_story") return "Growth Story";
  if (type === "real_world_experience") return "Real World";
  return type.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function variantFromElement(element: ApiStackElement, intensity: string): StackVariant {
  const duration =
    intensity === "micro" ? "1–2 min" : intensity === "light" ? "5–10 min" : "15–20 min";
  return {
    title: element.title,
    description: element.explanation.whyThis,
    duration,
  };
}

export function mapStackFromVariants(
  variants: ApiStackVariants,
  fallback?: ApiIdentityStack | null,
): StackElement[] {
  const full = variants.full?.stack ?? fallback;
  if (!full) return [];

  const lightById = new Map(
    (variants.light?.stack.elements ?? []).map((el) => [el.id, el]),
  );
  const microById = new Map(
    (variants.micro?.stack.elements ?? []).map((el) => [el.id, el]),
  );

  return full.elements.map((element) => {
    const light = lightById.get(element.id) ?? element;
    const micro = microById.get(element.id) ?? element;
    return {
      id: element.id,
      type: elementTypeLabel(element.type),
      source: element.sourceBadge,
      action: "Mark as done",
      why: element.explanation.whyThis,
      whyNow: element.explanation.whyNow,
      howItCloses: element.explanation.howReducesGap,
      variants: {
        FULL: variantFromElement(element, "full"),
        LIGHT: variantFromElement(light, "light"),
        MICRO: variantFromElement(micro, "micro"),
      },
    };
  });
}

export function mapStackFromActive(stack: ApiIdentityStack): StackElement[] {
  return mapStackFromVariants({}, stack);
}

export function mapBottleneck(packet?: ApiBottleneckPacket | null) {
  if (!packet) {
    return {
      name: "No bottleneck yet",
      diagnosis: "Complete onboarding and gather evidence to surface a bottleneck.",
      confidence: "low" as const,
      evidence: [] as string[],
    };
  }
  const confidence =
    packet.confidence >= 0.7 ? "high" : packet.confidence >= 0.4 ? "medium" : "low";
  return {
    name: packet.bottleneck.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()),
    diagnosis: `Primary growth friction: ${packet.bottleneck}.`,
    confidence: confidence as "high" | "medium" | "low",
    evidence: packet.supporting_evidence.slice(0, 4),
  };
}

export function mapLedgerEntry(entry: ApiLedgerEntry): LedgerEntry {
  const family = entry.hypothesisFamily.replace(/_/g, " ");
  return {
    id: entry.id,
    verdict: entry.verdict,
    hypothesis: `Hypothesis ${entry.hypothesisId} · ${family}`,
    family,
    deliveredAt: entry.timestamp,
    delivered: `${entry.action} · ${family}`,
    outcomeWindow: "14-day dismissal window / 7-day outcome window",
    evidence: entry.note ?? `Recorded as ${entry.action}`,
    ...(entry.unlearningTriggered
      ? {
          adaptation:
            entry.note ??
            "System Unlearning: failed lens deprioritized; switched to Micro-Action.",
        }
      : {}),
  };
}

export function mapUnlearningFromLedger(entries: ApiLedgerEntry[]): Unlearning | null {
  const hit = entries.find((e) => e.unlearningTriggered);
  if (!hit) return null;
  return {
    hypothesis: `${hit.hypothesisFamily} prompts will close the gap`,
    adaptation:
      hit.note ??
      "System Unlearning: failed lens −40%; switched to Micro-Action.",
  };
}

export function mapDashboardSummary(summary: ApiDashboardSummary) {
  const labels = Object.fromEntries(
    summary.declaredSelf.attributes.map((a) => [a.id, a.label]),
  );
  return {
    gap: mapGap(summary.gap, labels),
    declaredSelf: mapDeclaredSelfToUi(summary.declaredSelf),
    capacity: summary.capacity,
    bottleneck: mapBottleneck(summary.bottleneck),
  };
}
