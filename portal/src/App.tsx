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
    <div className="min-h-screen">
      <header className="border-b border-white/5 bg-gradient-to-b from-white/[0.04] to-transparent backdrop-blur-sm sticky top-0 z-10">
        <div className="mx-auto max-w-7xl px-6 py-4 flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="h-9 w-9 rounded-xl bg-gradient-to-br from-indigo-500 via-orange-500 to-teal-500 flex items-center justify-center shadow-lg shadow-indigo-500/30">
              <BrainCircuit className="h-5 w-5 text-white" />
            </div>
            <div>
              <div className="text-base font-bold tracking-tight text-white">
                WhoIsWhat · Portal
              </div>
              <div className="text-[0.72rem] text-[color:var(--color-muted)] tracking-wide">
                K taxonomy · HOSS F-scale · Meeting advisor
              </div>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <HealthBadges />
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-6 py-8 space-y-6">
        {state.topLevelError && (
          <div className="rounded-xl border border-rose-400/30 bg-rose-500/10 p-4 text-sm text-rose-200 whitespace-pre-wrap">
            <span className="font-semibold">Request failed.</span> {state.topLevelError}
          </div>
        )}

        <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_22rem]">
          <div className="space-y-6">
            <Card>
              <CardHeader
                title="Plan a meeting"
                subtitle="Fan-out classification + grounded advice"
              />
              <CardBody>
                <SubjectForm loading={state.loading} onSubmit={handleSubmit} />
              </CardBody>
            </Card>

            <div className="grid gap-6 md:grid-cols-2">
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

          <aside>
            <HistoryPanel refreshToken={historyToken} onSelect={selectHistory} />
          </aside>
        </div>

        <footer className="pt-8 pb-4 text-center text-[0.72rem] text-[color:var(--color-muted)]">
          Built with React · Vite · Tailwind · Flask · OpenAI
        </footer>
      </main>
    </div>
  )
}
