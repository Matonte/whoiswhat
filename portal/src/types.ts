export type ServiceName = "whoiswhat" | "whoishoss" | "advisor"

export interface KProfile {
  classification_code: string
  classification_label: string
  awareness_failure_score: number
  intent_failure_score: number
  control_failure_score: number
  short_rationale: string
}

export interface HossTraits {
  square: number
  punisher: number
  power: number
  skull: number
}

export interface HossProfile {
  id?: number
  name: string
  source: string
  input_summary: string | null
  f_scale_items: Record<string, number>
  traits: HossTraits
  hoss_score: number
  hoss_level: number
  display_label: string
  internal_label: string
  explanation: string
  _reused?: boolean
}

export type RiskLevel = "low" | "medium" | "high"

export interface MeetingAdvice {
  risk_level: RiskLevel
  key_observations: string
  do: string[]
  dont: string[]
  opening_move: string
  watchpoints: string[]
  escalation_plan: string
}

export interface MeetingContext {
  setting: string
  stakes: RiskLevel | string
  your_role: string | null
  goals: string | null
}

export interface AdviseRequest {
  subject_name: string
  source_hint?: string | null
  notes?: string | null
  context: MeetingContext
}

export interface AdviseResponse {
  id: number
  subject_name: string
  source_hint: string | null
  context: MeetingContext
  k_profile: KProfile | null
  k_error: string | null
  hoss_profile: HossProfile | null
  hoss_error: string | null
  advice: MeetingAdvice
  risk_level: RiskLevel
  model: string
}

export interface AdviceRunSummary {
  id: number
  subject_name: string
  source_hint: string | null
  risk_level: RiskLevel | null
  model: string
  created_at: string
}

export interface HealthStatus {
  ok: boolean
  raw: unknown
  detail?: string
}
