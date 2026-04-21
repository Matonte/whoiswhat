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
        "animate-pulse rounded-md bg-white/[0.05]",
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
    <div className="rounded-lg border border-white/10 bg-white/[0.04] px-2.5 py-2 flex flex-col gap-0.5">
      <span className="text-[0.68rem] uppercase tracking-[0.1em] text-[color:var(--color-muted)]">
        {label}
      </span>
      <span
        className="text-sm font-semibold"
        style={{ color: accent ?? "var(--color-ink)" }}
      >
        {value}
      </span>
    </div>
  )
}
