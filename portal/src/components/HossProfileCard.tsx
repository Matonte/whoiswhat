import { Flame, RotateCcw } from "lucide-react"
import { Card, CardBody, CardHeader } from "@/components/ui/Card"
import { Badge } from "@/components/ui/Badge"
import { Pill, Skeleton } from "@/components/ui/Misc"
import type { HossProfile } from "@/types"

interface Props {
  profile: HossProfile | null
  loading: boolean
  error: string | null
}

function HossRadar({ t }: { t: HossProfile["traits"] }) {
  const dims = [
    { key: "square", label: "Square", value: t.square },
    { key: "punisher", label: "Punisher", value: t.punisher },
    { key: "power", label: "Power", value: t.power },
    { key: "skull", label: "Skull", value: t.skull },
  ]
  const cx = 100
  const cy = 100
  const r = 78
  const max = 6
  const angle = (i: number) => (Math.PI / 2) * i - Math.PI / 2
  const point = (i: number, v: number) => {
    const a = angle(i)
    const scale = Math.max(0, Math.min(max, v)) / max
    return [cx + Math.cos(a) * r * scale, cy + Math.sin(a) * r * scale] as const
  }

  const polyPts = dims.map((d, i) => point(i, d.value).join(",")).join(" ")
  const ringPts = (scale: number) =>
    dims
      .map((_, i) => {
        const a = angle(i)
        return [cx + Math.cos(a) * r * scale, cy + Math.sin(a) * r * scale].join(",")
      })
      .join(" ")

  return (
    <div className="flex items-center justify-center">
      <svg viewBox="0 0 200 200" width="180" height="180" aria-hidden>
        {[0.25, 0.5, 0.75, 1].map((s) => (
          <polygon
            key={s}
            points={ringPts(s)}
            fill="none"
            stroke="rgba(79,255,196,0.12)"
            strokeWidth={1}
          />
        ))}
        {dims.map((_, i) => {
          const [x, y] = point(i, max)
          return (
            <line
              key={i}
              x1={cx}
              y1={cy}
              x2={x}
              y2={y}
              stroke="rgba(79,255,196,0.12)"
              strokeWidth={1}
            />
          )
        })}
        <polygon
          points={polyPts}
          fill="rgba(255, 184, 112, 0.18)"
          stroke="#ffb870"
          strokeWidth={1.5}
        />
        {dims.map((d, i) => {
          const [x, y] = point(i, max * 1.08)
          const anchor = i === 1 ? "start" : i === 3 ? "end" : "middle"
          return (
            <text
              key={d.key}
              x={x}
              y={y + 3}
              textAnchor={anchor}
              fontSize={10}
              fill="#62c9a8"
              style={{ fontFamily: "var(--font-sans)" }}
            >
              {d.label} {d.value.toFixed(1)}
            </text>
          )
        })}
      </svg>
    </div>
  )
}

export function HossProfileCard({ profile, loading, error }: Props) {
  return (
    <Card>
      <CardHeader
        accent="var(--color-whoishoss)"
        title={
          <span className="inline-flex items-center gap-2">
            <Flame className="h-3.5 w-3.5 text-[color:var(--color-whoishoss)]" />
            HOSS Archetype
          </span>
        }
        subtitle="WhoIsHoss · port 5002"
        right={
          profile?._reused && (
            <Badge className="border-[color:var(--color-whoishoss)] bg-[rgba(255,184,112,0.12)] text-[color:var(--color-whoishoss)]">
              <RotateCcw className="h-3 w-3" /> reused
            </Badge>
          )
        }
      />
      <CardBody>
        {loading && (
          <div className="space-y-3">
            <Skeleton className="h-8 w-1/2" />
            <Skeleton className="h-4 w-5/6" />
            <div className="flex justify-center">
              <Skeleton className="h-36 w-36 rounded-full" />
            </div>
          </div>
        )}

        {!loading && error && (
          <div className="rounded-[var(--radius-inner)] border border-[color:var(--danger-muted)] bg-[rgba(140,53,64,0.2)] p-3 text-sm text-[color:var(--danger)] whitespace-pre-wrap font-[family-name:var(--font-mono)]">
            {error}
          </div>
        )}

        {!loading && !error && !profile && (
          <div className="text-sm text-[color:var(--fg-dim)]">
            Submit to classify along the HOSS F-scale archetype.
          </div>
        )}

        {!loading && !error && profile && (
          <div className="space-y-3.5">
            <div>
              <div className="text-xl font-bold tracking-tight text-[color:var(--fg)] leading-tight font-[family-name:var(--font-display)] uppercase tracking-[0.06em]">
                {profile.display_label}
              </div>
              <div className="text-xs text-[color:var(--fg-dim)] mt-0.5 font-[family-name:var(--font-mono)]">
                level {profile.hoss_level} · {profile.internal_label}
              </div>
            </div>
            <div className="grid grid-cols-2 gap-2">
              <Pill
                label="HOSS Score"
                value={profile.hoss_score.toFixed(2) + " / 5"}
                accent="var(--warn)"
              />
              <Pill label="Level" value={`${profile.hoss_level} / 5`} accent="var(--warn)" />
            </div>
            <HossRadar t={profile.traits} />
            <p className="text-sm text-[color:var(--fg-muted)] leading-relaxed">
              {profile.explanation}
            </p>
          </div>
        )}
      </CardBody>
    </Card>
  )
}
