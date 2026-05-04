import { useMemo, useState } from "react"
import { BrainCircuit } from "lucide-react"
import { advise, ApiError } from "@/api"
import { Card, CardBody, CardHeader } from "@/components/ui/Card"
import { HealthBadges } from "@/components/HealthBadges"
import { SubjectForm } from "@/components/SubjectForm"
import { KProfileCard } from "@/components/KProfileCard"
import { HossProfileCard } from "@/components/HossProfileCard"
import { AdviceCard } from "@/components/AdviceCard"
import { HistoryPanel } from "@/components/HistoryPanel"
import type { AdviseRequest, AdviseResponse } from "@/types"

interface AppState {
  loading: boolean
  result: AdviseResponse | null
  topLevelError: string | null
}

const EMPTY: AppState = { loading: false, result: null, topLevelError: null }

export default function App() {
  const [state, setState] = useState<AppState>(EMPTY)
  const [historyToken, setHistoryToken] = useState(0)

  const handleSubmit = async (req: AdviseRequest) => {
    setState({ loading: true, result: null, topLevelError: null })
    try {
      const result = await advise(req)
      setState({ loading: false, result, topLevelError: null })
      setHistoryToken((t) => t + 1)
    } catch (e) {
      const msg =
        e instanceof ApiError
          ? `${e.message}${e.detail ? `\n\n${e.detail}` : ""}`
          : (e as Error).message
      setState({ loading: false, result: null, topLevelError: msg })
    }
  }

  const kError = useMemo(
    () => state.result?.k_error ?? null,
    [state.result]
  )
  const hossError = useMemo(
    () => state.result?.hoss_error ?? null,
    [state.result]
  )

  const selectHistory = (r: AdviseResponse) => {
    setState({ loading: false, result: r, topLevelError: null })
    window.scrollTo({ top: 0, behavior: "smooth" })
  }

  return (
    <div className="min-h-full">
      <header className="border-b border-[color:var(--border)] shadow-[0_1px_0_0_var(--accent-glow)] sticky top-0 z-10 bg-[color:var(--bg-base)]/95 backdrop-blur-[2px]">
        <div className="mx-auto max-w-[1320px] px-6 py-5 flex flex-wrap items-end justify-between gap-6">
          <div className="min-w-0">
            <h1 className="m-0 font-[family-name:var(--font-display)] text-[1.05rem] font-bold uppercase tracking-[0.2em] text-[color:var(--accent)] [text-shadow:0_0_8px_var(--accent-glow),0_0_24px_rgba(79,255,196,0.35)] flex flex-wrap items-center gap-x-1 gap-y-1">
              <span className="inline-flex items-center gap-2">
                <span
                  aria-hidden
                  className="inline-flex h-9 w-9 shrink-0 items-center justify-center border border-[color:var(--border-strong)] bg-[color:var(--panel)] text-[color:var(--accent)]"
                  style={{
                    clipPath:
                      "polygon(8px 0,100% 0,100% calc(100% - 8px),calc(100% - 8px) 100%,0 100%,0 8px)",
                  }}
                >
                  <BrainCircuit className="h-5 w-5" strokeWidth={2} />
                </span>
                Contact Advisor
              </span>
              <span className="portal-wordmark-tag">Portal</span>
            </h1>
            <p className="subtitle mt-2 max-w-[52em] text-[color:var(--fg-muted)] text-[1.05rem] leading-snug tracking-[0.04em] [text-shadow:0_0_6px_rgba(79,255,196,0.18)]">
              K taxonomy · HOSS F-scale · Meeting advisor — same phosphor HUD vibe as Resume Agent.
            </p>
          </div>
          <div className="flex flex-wrap gap-3 justify-end">
            <HealthBadges />
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-[1320px] px-6 py-7 space-y-[18px]">
        {state.topLevelError && (
          <div className="portal-panel px-[22px] py-4 border border-[color:var(--danger-muted)] bg-[rgba(140,53,64,0.2)] text-sm text-[color:var(--danger)] whitespace-pre-wrap">
            <span className="font-[family-name:var(--font-display)] text-[0.68rem] uppercase tracking-[0.14em] text-[color:var(--accent)]">
              Request failed.
            </span>{" "}
            {state.topLevelError}
          </div>
        )}

        <div className="grid gap-[18px] lg:grid-cols-[minmax(0,1fr)_22rem]">
          <div className="space-y-[18px]">
            <Card>
              <CardHeader
                title="Plan a meeting"
                subtitle="Fan-out classification + grounded advice"
              />
              <CardBody>
                <SubjectForm loading={state.loading} onSubmit={handleSubmit} />
              </CardBody>
            </Card>

            <div className="grid gap-[18px] md:grid-cols-2">
              <KProfileCard
                profile={state.result?.k_profile ?? null}
                loading={state.loading}
                error={kError}
              />
              <HossProfileCard
                profile={state.result?.hoss_profile ?? null}
                loading={state.loading}
                error={hossError}
              />
            </div>

            <AdviceCard
              advice={state.result?.advice ?? null}
              loading={state.loading}
              error={null}
              model={state.result?.model ?? null}
            />
          </div>

          <aside className="space-y-[18px]">
            <HistoryPanel refreshToken={historyToken} onSelect={selectHistory} />
          </aside>
        </div>

        <footer className="footer pt-6 pb-8 text-center text-[0.72rem] text-[color:var(--fg-dim)] font-[family-name:var(--font-mono)] tracking-[0.06em]">
          Portal · React · Vite · Tailwind · Flask siblings · styled like Resume Agent
        </footer>
      </main>
    </div>
  )
}
