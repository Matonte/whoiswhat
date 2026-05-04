import type { HTMLAttributes } from "react"
import { cn } from "@/lib/utils"

export function Separator({ className }: { className?: string }) {
  return <div className={cn("h-px bg-white/10 my-4", className)} />
}

export function Skeleton({
  className,
  ...props
}: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "animate-pulse rounded-[var(--radius-inner)] bg-[color:var(--panel-raised)] border border-[color:var(--border)]",
        className
      )}
      {...props}
    />
  )
}

export function Spinner({ className }: { className?: string }) {
  return (
    <svg
      className={cn("animate-spin h-4 w-4", className)}
      viewBox="0 0 24 24"
      fill="none"
      aria-hidden
    >
      <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" strokeOpacity="0.25" />
      <path
        d="M22 12a10 10 0 0 1-10 10"
        stroke="currentColor"
        strokeWidth="3"
        strokeLinecap="round"
      />
    </svg>
  )
}

export function Pill({
  label,
  value,
  accent,
}: {
  label: string
  value: string | number
  accent?: string
}) {
  return (
    <div className="rounded-[var(--radius-inner)] border border-[color:var(--border-strong)] bg-[color:var(--panel-raised)] px-2.5 py-2 flex flex-col gap-0.5">
      <span className="text-[0.68rem] uppercase tracking-[0.1em] text-[color:var(--fg-dim)] font-[family-name:var(--font-mono)]">
        {label}
      </span>
      <span
        className="text-sm font-semibold font-[family-name:var(--font-mono)]"
        style={{ color: accent ?? "var(--fg)" }}
      >
        {value}
      </span>
    </div>
  )
}
