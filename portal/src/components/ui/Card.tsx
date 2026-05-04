import { forwardRef, type HTMLAttributes, type ReactNode } from "react"
import { cn } from "@/lib/utils"

export const Card = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn("portal-panel", className)} {...props} />
  )
)
Card.displayName = "Card"

export function CardHeader({
  className,
  title,
  subtitle,
  accent,
  right,
}: {
  className?: string
  title: ReactNode
  subtitle?: ReactNode
  accent?: string
  right?: ReactNode
}) {
  return (
    <div
      className={cn(
        "flex items-start justify-between gap-3 px-[22px] pt-5 pb-4 border-b border-[color:var(--border)] shadow-[0_1px_0_0_var(--accent-glow)]",
        className
      )}
    >
      <div className="flex items-start gap-3 min-w-0">
        {accent && (
          <span
            aria-hidden
            className="mt-1.5 h-2 w-2 rounded-[1px] flex-shrink-0 border border-[color:var(--border-strong)]"
            style={{
              backgroundColor: accent,
              boxShadow: `0 0 10px ${accent}`,
            }}
          />
        )}
        <div className="min-w-0">
          <div className="font-[family-name:var(--font-display)] text-[0.68rem] font-semibold uppercase tracking-[0.16em] text-[color:var(--accent)] truncate [text-shadow:0_0_8px_var(--accent-glow)]">
            {title}
          </div>
          {subtitle && (
            <div className="font-[family-name:var(--font-mono)] text-[0.72rem] uppercase tracking-[0.08em] text-[color:var(--fg-dim)] mt-1 truncate">
              {subtitle}
            </div>
          )}
        </div>
      </div>
      {right && <div className="flex-shrink-0">{right}</div>}
    </div>
  )
}

export function CardBody({
  className,
  ...props
}: HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn("px-[22px] py-4 text-sm text-[color:var(--fg-muted)]", className)} {...props} />
  )
}
