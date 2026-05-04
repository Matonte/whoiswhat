import type { HTMLAttributes } from "react"
import { cn } from "@/lib/utils"
import type { RiskLevel } from "@/types"

export function Badge({
  className,
  ...props
}: HTMLAttributes<HTMLSpanElement>) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-[var(--radius-inner)] border border-[color:var(--border-strong)] bg-[color:var(--panel-raised)] px-2.5 py-1 text-[0.72rem] font-medium uppercase tracking-[0.08em] text-[color:var(--fg-muted)] font-[family-name:var(--font-mono)]",
        className
      )}
      {...props}
    />
  )
}

const riskStyles: Record<RiskLevel, string> = {
  low: "bg-[rgba(79,255,196,0.1)] text-[color:var(--accent)] border-[color:var(--accent-dim)]",
  medium: "bg-[rgba(255,208,96,0.08)] text-[color:var(--warn)] border-[color:var(--warn)]",
  high: "bg-[rgba(255,107,122,0.12)] text-[color:var(--danger)] border-[color:var(--danger-muted)]",
}

export function RiskBadge({ level }: { level: RiskLevel | null | undefined }) {
  const key = (level || "low") as RiskLevel
  return (
    <Badge className={cn("font-bold", riskStyles[key])}>
      <span
        aria-hidden
        className={cn(
          "h-1.5 w-1.5 rounded-full",
          key === "high"
            ? "bg-[color:var(--danger)]"
            : key === "medium"
              ? "bg-[color:var(--warn)]"
              : "bg-[color:var(--accent)] shadow-[0_0_8px_var(--accent-glow)]"
        )}
      />
      {(level || "unknown") + " risk"}
    </Badge>
  )
}
