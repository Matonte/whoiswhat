import { useEffect, useState } from "react"
import { fetchAllHealth } from "@/api"
import type { HealthStatus } from "@/types"
import { cn } from "@/lib/utils"

const services = [
  { key: "contact_advisor", label: "Contact Advisor", port: 5000, color: "var(--color-contact-advisor)" },
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
              "inline-flex items-center gap-1.5 rounded-[var(--radius-inner)] border px-2.5 py-1 text-[0.72rem] font-[family-name:var(--font-mono)] tracking-[0.04em]",
              ok
                ? "border-[color:var(--border-strong)] bg-[color:var(--panel-raised)] text-[color:var(--accent)]"
                : "border-[color:var(--danger-muted)] bg-[rgba(140,53,64,0.25)] text-[color:var(--danger)]"
            )}
          >
            <span
              aria-hidden
              className={cn(
                "h-1.5 w-1.5 rounded-[1px]",
                ok ? "bg-[color:var(--accent)] animate-pulse shadow-[0_0_8px_var(--accent-glow)]" : "bg-[color:var(--danger)]"
              )}
            />
            {s.label}
            <span className="text-[color:var(--fg-dim)]">:{s.port}</span>
          </div>
        )
      })}
    </div>
  )
}
