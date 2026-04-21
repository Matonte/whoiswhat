import type {
  AdviceRunSummary,
  AdviseRequest,
  AdviseResponse,
  HealthStatus,
  KProfile,
  HossProfile,
} from "./types"

const WHOISWHAT_BASE = "/api/whoiswhat"
const WHOISHOSS_BASE = "/api/whoishoss"
const ADVISOR_BASE = "/api/advisor"

interface ApiErrorPayload {
  error?: string
  detail?: string
}

export class ApiError extends Error {
  status: number
  detail?: string

  constructor(status: number, message: string, detail?: string) {
    super(message)
    this.name = "ApiError"
    this.status = status
    this.detail = detail
  }
}

async function parseOrThrow<T>(r: Response): Promise<T> {
  if (!r.ok) {
    let payload: ApiErrorPayload = {}
    try {
      payload = (await r.json()) as ApiErrorPayload
    } catch {
      const text = await r.text().catch(() => "")
      throw new ApiError(r.status, text || `HTTP ${r.status}`)
    }
    throw new ApiError(r.status, payload.error || `HTTP ${r.status}`, payload.detail)
  }
  return (await r.json()) as T
}

export async function fetchHealth(
  base: string
): Promise<HealthStatus> {
  try {
    const r = await fetch(`${base}/health`)
    const body = await r.json().catch(() => ({}))
    return { ok: r.ok, raw: body }
  } catch (e) {
    return { ok: false, raw: null, detail: (e as Error).message }
  }
}

export async function fetchAllHealth(): Promise<Record<string, HealthStatus>> {
  const [w, h, a] = await Promise.all([
    fetchHealth(WHOISWHAT_BASE),
    fetchHealth(WHOISHOSS_BASE),
    fetchHealth(ADVISOR_BASE),
  ])
  return { whoiswhat: w, whoishoss: h, advisor: a }
}

export async function classifyK(
  subject_name: string,
  character?: string | null
): Promise<KProfile> {
  const r = await fetch(`${WHOISWHAT_BASE}/api/v1/classify`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ subject_name, character }),
  })
  return parseOrThrow<KProfile>(r)
}

export async function classifyHoss(body: {
  name: string
  source?: string | null
  input_summary?: string | null
}): Promise<HossProfile> {
  const r = await fetch(`${WHOISHOSS_BASE}/api/v1/hoss/classify`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  })
  return parseOrThrow<HossProfile>(r)
}

export async function advise(req: AdviseRequest): Promise<AdviseResponse> {
  const r = await fetch(`${ADVISOR_BASE}/api/v1/advise`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  })
  return parseOrThrow<AdviseResponse>(r)
}

export async function listAdvice(limit = 25): Promise<AdviceRunSummary[]> {
  const r = await fetch(`${ADVISOR_BASE}/api/v1/advice?limit=${limit}`)
  return parseOrThrow<AdviceRunSummary[]>(r)
}

export async function getAdvice(id: number): Promise<AdviseResponse> {
  const r = await fetch(`${ADVISOR_BASE}/api/v1/advice/${id}`)
  return parseOrThrow<AdviseResponse>(r)
}
