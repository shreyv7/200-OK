import type { ApiDeclaredSelf } from "./types";

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
