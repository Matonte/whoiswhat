import {
  AlertTriangle,
  Check,
  Compass,
  Eye,
  LifeBuoy,
  Lightbulb,
  X,
} from "lucide-react"
import { Card, CardBody, CardHeader } from "@/components/ui/Card"
import { RiskBadge } from "@/components/ui/Badge"
import { Skeleton } from "@/components/ui/Misc"
import type { MeetingAdvice } from "@/types"

interface Props {
  advice: MeetingAdvice | null
  loading: boolean
  error: string | null
  model: string | null
}

function Section({
  icon,
  label,
  children,
}: {
  icon: React.ReactNode
  label: string
  children: React.ReactNode
}) {
  return (
    <div>
      <div className="flex items-center gap-2 mb-2 text-[0.75rem] font-semibold uppercase tracking-[0.1em] text-[color:var(--color-muted)]">
        <span className="text-indigo-300">{icon}</span>
        {label}
      </div>
      {children}
    </div>
  )
}

function BulletList({
  items,
  icon,
  iconClass,
}: {
  items: string[]
  icon: React.ReactNode
  iconClass: string
}) {
  if (!items?.length)
    return <div className="text-sm text-[color:var(--color-muted)]">—</div>
  return (
    <ul className="space-y-1.5">
      {items.map((t, i) => (
        <li
          key={i}
          className="flex items-start gap-2 text-sm text-ink-soft leading-relaxed"
        >
          <span className={`mt-1 flex-shrink-0 ${iconClass}`}>{icon}</span>
          <span>{t}</span>
        </li>
      ))}
    </ul>
  )
}

export function AdviceCard({ advice, loading, error, model }: Props) {
  return (
    <Card>
      <CardHeader
        accent="var(--color-advisor)"
        title={
          <span className="inline-flex items-center gap-2">
            <Compass className="h-3.5 w-3.5 text-teal-300" />
            Meeting guidance
          </span>
        }
        subtitle={model ? `Advisor · ${model}` : "Advisor · port 5003"}
        right={advice && <RiskBadge level={advice.risk_level} />}
      />
      <CardBody>
        {loading && (
          <div className="space-y-3">
            <Skeleton className="h-4 w-3/4" />
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-5/6" />
            <div className="grid grid-cols-2 gap-3 pt-2">
              <Skeleton className="h-24" />
              <Skeleton className="h-24" />
            </div>
          </div>
        )}

        {!loading && error && (
          <div className="rounded-lg border border-rose-400/30 bg-rose-500/10 p-3 text-sm text-rose-200 whitespace-pre-wrap">
            {error}
          </div>
        )}

        {!loading && !error && !advice && (
          <div className="text-sm text-[color:var(--color-muted)]">
            Submit to generate a grounded meeting brief from both profiles and your context.
          </div>
        )}

        {!loading && !error && advice && (
          <div className="space-y-5">
            <p className="text-[0.95rem] leading-relaxed text-ink">
              {advice.key_observations}
            </p>

            <div className="grid gap-5 md:grid-cols-2">
              <Section
                icon={<Check className="h-3.5 w-3.5" />}
                label="Do"
              >
                <BulletList
                  items={advice.do}
                  icon={<Check className="h-3.5 w-3.5" />}
                  iconClass="text-emerald-400"
                />
              </Section>
              <Section
                icon={<X className="h-3.5 w-3.5" />}
                label="Don't"
              >
                <BulletList
                  items={advice.dont}
                  icon={<X className="h-3.5 w-3.5" />}
                  iconClass="text-rose-400"
                />
              </Section>
            </div>

            <Section
              icon={<Lightbulb className="h-3.5 w-3.5" />}
              label="Opening move"
            >
              <p className="text-sm text-ink leading-relaxed">{advice.opening_move}</p>
            </Section>

            <div className="grid gap-5 md:grid-cols-2">
              <Section
                icon={<Eye className="h-3.5 w-3.5" />}
                label="Watch for"
              >
                <BulletList
                  items={advice.watchpoints}
                  icon={<AlertTriangle className="h-3.5 w-3.5" />}
                  iconClass="text-amber-400"
                />
              </Section>
              <Section
                icon={<LifeBuoy className="h-3.5 w-3.5" />}
                label="If it goes sideways"
              >
                <p className="text-sm text-ink-soft leading-relaxed">
                  {advice.escalation_plan}
                </p>
              </Section>
            </div>
          </div>
        )}
      </CardBody>
    </Card>
  )
}
