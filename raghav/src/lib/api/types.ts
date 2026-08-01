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

export interface VectorSearchResultItem {
  id: string;
  collection: string;
  score: number;
  payload: Record<string, any>;
}

export interface SemanticSearchResponse {
  query: string;
  total_results: number;
  vector_store_active: boolean;
  results: VectorSearchResultItem[];
}

export interface QdrantStatusResponse {
  enabled: boolean;
  url: string | null;
  collection_prefix: string;
  collections: string[];
}

export interface ApiPartnerProfile {
  id: string;
  name: string;
  stage: string;
  goal: string;
  matchReason?: string;
}
