export interface ApiIdentityMarker {
  id: string;
  label: string;
  description?: string | null;
}

export interface ApiIdentityAttribute {
  id: string;
  label: string;
  weight: number;
  targetWeeklyPoints: number;
  markers: ApiIdentityMarker[];
}

export interface ApiDeclaredSelf {
  id: string;
  userId: string;
  version: number;
  attributes: ApiIdentityAttribute[];
  createdAt: string;
  confirmedAt?: string | null;
}

export interface ApiOnboardingTurnResponse {
  sessionId: string;
  nextQuestion?: string | null;
  draft?: ApiDeclaredSelf | null;
  done: boolean;
}

export interface ApiMeUser {
  id: string;
  email?: string | null;
  fullName?: string | null;
  capacity?: number;
}

export type ApiSourceBadge = "Live web" | "Cached web" | "Curated fallback";

export interface ApiStackExplanation {
  whyThis: string;
  whyNow: string;
  howReducesGap: string;
}

export interface ApiFeedItem {
  id: string;
  kind: "low_value" | "neutral" | "resource";
  title: string;
  tag: string;
  url?: string | null;
  sourceBadge?: ApiSourceBadge | null;
  thumbnailUrl?: string | null;
  channelTitle?: string | null;
  durationSeconds?: number | null;
  explanation?: ApiStackExplanation | null;
  metadata: Record<string, unknown>;
}

export interface ApiFeedPage {
  items: ApiFeedItem[];
  nextCursor?: string | null;
}

export interface ApiPreparedIntervention {
  stack: {
    bottleneck: string;
    elements: Array<{
      id: string;
      type: string;
      title: string;
      sourceBadge: ApiSourceBadge;
      explanation: ApiStackExplanation;
    }>;
  };
}
