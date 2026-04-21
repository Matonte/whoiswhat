import { History, RefreshCw } from "lucide-react"
import { useCallback, useEffect, useState } from "react"
import { getAdvice, listAdvice } from "@/api"
import { Button } from "@/components/ui/Button"
import { Card, CardBody, CardHeader } from "@/components/ui/Card"
import { RiskBadge } from "@/components/ui/Badge"
import { Skeleton } from "@/components/ui/Misc"
import { formatTimestamp } from "@/lib/utils"
import type { AdviceRunSummary, AdviseResponse } from "@/types"

interface Props {
  refreshToken: number
  onSelect(r: AdviseResponse): void
}

export function HistoryPanel({ refreshToken, onSelect }: Props) {
  const [rows, setRows] = useState<AdviceRunSummary[] | null>(null)
  const [loading, setLoading] = useState(false)
  const [pickedId, setPickedId] = useState<number | null>(null)

  const refresh = useCallback(() => {
    setLoading(true)
    listAdvice(25)
      .then(setRows)
      .catch(() => setRows([]))
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    refresh()
  }, [refresh, refreshToken])

  const pick = (id: number) => {
    setPickedId(id)
    getAdvice(id)
      .then(onSelect)
      .catch(() => {})
  }

  return (
    <Card>
      <CardHeader
        accent="var(--color-advisor)"
        title={
          <span className="inline-flex items-center gap-2">
            <History className="h-3.5 w-3.5 text-teal-300" />
            Recent advice runs
          </span>
        }
        subtitle={rows ? `${rows.length} stored` : undefined}
        right={
          <Button
            variant="ghost"
            size="sm"
            onClick={refresh}
            disabled={loading}
            aria-label="Refresh"
          >
            <RefreshCw className={loading ? "h-3.5 w-3.5 animate-spin" : "h-3.5 w-3.5"} />
          </Button>
        }
      />
      <CardBody className="p-0">
        {!rows && loading && (
          <div className="p-4 space-y-2">
            {[...Array(3)].map((_, i) => (
              <Skeleton key={i} className="h-12 w-full" />
            ))}
          </div>
        )}
        {rows && rows.length === 0 && (
          <div className="p-5 text-sm text-[color:var(--color-muted)]">
            No advice runs yet. Submit the form to create one.
          </div>
        )}
        {rows && rows.length > 0 && (
          <ul className="divide-y divide-white/5 max-h-[28rem] overflow-y-auto">
            {rows.map((r) => (
              <li key={r.id}>
                <button
                  type="button"
                  onClick={() => pick(r.id)}
                  className={`w-full text-left px-5 py-3 flex items-center justify-between gap-3 hover:bg-white/[0.03] transition ${
                    pickedId === r.id ? "bg-white/[0.05]" : ""
                  }`}
                >
                  <div className="min-w-0">
                    <div className="text-sm font-medium text-white truncate">
                      {r.subject_name}
                    </div>
                    <div className="text-[0.7rem] text-[color:var(--color-muted)] truncate">
                      {r.source_hint || "—"} · {formatTimestamp(r.created_at)}
                    </div>
                  </div>
                  <RiskBadge level={r.risk_level} />
                </button>
              </li>
            ))}
          </ul>
        )}
      </CardBody>
    </Card>
  )
}
