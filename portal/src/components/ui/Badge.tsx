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
        "inline-flex items-center gap-1.5 rounded-full border border-white/10 bg-white/[0.05] px-2.5 py-1 text-[0.72rem] font-medium uppercase tracking-[0.08em] text-ink-soft",
        className
      )}
      {...props}
    />
  )
}

const riskStyles: Record<RiskLevel, string> = {
  low: "bg-emerald-500/15 text-emerald-300 border-emerald-400/30",
  medium: "bg-amber-500/15 text-amber-300 border-amber-400/30",
  high: "bg-rose-500/15 text-rose-300 border-rose-400/30",
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
            ? "bg-rose-400"
            : key === "medium"
              ? "bg-amber-400"
              : "bg-emerald-400"
        )}
      />
      {(level || "unknown") + " risk"}
    </Badge>
  )
}
