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

export interface ApiOnboardingQuestion {
  id: string;
  prompt: string;
  hint: string;
  options: string[];
}

export interface ApiOnboardingPersona {
  id: string;
  title: string;
  description: string;
  outcome: string;
  questions: ApiOnboardingQuestion[];
}

export interface ApiMeUser {
  id: string;
  email?: string | null;
  fullName?: string | null;
  capacity?: number;
}
