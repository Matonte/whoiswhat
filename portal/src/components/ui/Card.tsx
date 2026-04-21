import { forwardRef, type HTMLAttributes, type ReactNode } from "react"
import { cn } from "@/lib/utils"

export const Card = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        "rounded-2xl bg-white/[0.03] border border-white/10 backdrop-blur-sm shadow-xl shadow-black/30",
        className
      )}
      {...props}
    />
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
        "flex items-start justify-between gap-3 px-5 py-4 border-b border-white/5",
        className
      )}
    >
      <div className="flex items-start gap-3 min-w-0">
        {accent && (
          <span
            aria-hidden
            className="mt-1.5 h-2 w-2 rounded-full flex-shrink-0"
            style={{ backgroundColor: accent, boxShadow: `0 0 12px ${accent}` }}
          />
        )}
        <div className="min-w-0">
          <div className="text-sm font-semibold tracking-tight text-white truncate">
            {title}
          </div>
          {subtitle && (
            <div className="text-[0.72rem] uppercase tracking-[0.12em] text-[color:var(--color-muted)] mt-0.5 truncate">
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
  return <div className={cn("px-5 py-4 text-sm text-ink-soft", className)} {...props} />
}
