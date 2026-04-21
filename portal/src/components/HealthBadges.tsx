import { useEffect, useState } from "react"
import { fetchAllHealth } from "@/api"
import type { HealthStatus } from "@/types"
import { cn } from "@/lib/utils"

const services = [
  { key: "whoiswhat", label: "WhoIsWhat", port: 5000, color: "var(--color-whoiswhat)" },
  { key: "whoishoss", label: "WhoIsHoss", port: 5002, color: "var(--color-whoishoss)" },
  { key: "advisor", label: "Advisor", port: 5003, color: "var(--color-advisor)" },
] as const

export function HealthBadges() {
  const [state, setState] = useState<Record<string, HealthStatus> | null>(null)

  useEffect(() => {
    let alive = true
    const run = () => {
      fetchAllHealth().then((s) => alive && setState(s)).catch(() => {})
    }
    run()
    const interval = setInterval(run, 15_000)
    return () => {
      alive = false
      clearInterval(interval)
    }
  }, [])

  return (
    <div className="flex flex-wrap items-center gap-2">
      {services.map((s) => {
        const st = state?.[s.key]
        const ok = !!st?.ok
        return (
          <div
            key={s.key}
            title={ok ? "healthy" : st?.detail || "unreachable"}
            className={cn(
              "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[0.72rem] font-medium",
              ok
                ? "border-emerald-400/30 bg-emerald-500/10 text-emerald-300"
                : "border-rose-400/30 bg-rose-500/10 text-rose-300"
            )}
          >
            <span
              aria-hidden
              className={cn(
                "h-1.5 w-1.5 rounded-full",
                ok ? "bg-emerald-400 animate-pulse" : "bg-rose-400"
              )}
            />
            {s.label}
            <span className="text-[color:var(--color-muted)]">:{s.port}</span>
          </div>
        )
      })}
    </div>
  )
}
