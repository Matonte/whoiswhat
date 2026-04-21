import { Tags } from "lucide-react"
import { Card, CardBody, CardHeader } from "@/components/ui/Card"
import { Pill, Skeleton } from "@/components/ui/Misc"
import type { KProfile } from "@/types"

interface Props {
  profile: KProfile | null
  loading: boolean
  error: string | null
}

export function KProfileCard({ profile, loading, error }: Props) {
  return (
    <Card>
      <CardHeader
        accent="var(--color-whoiswhat)"
        title={
          <span className="inline-flex items-center gap-2">
            <Tags className="h-3.5 w-3.5 text-indigo-300" />
            K Taxonomy
          </span>
        }
        subtitle="WhoIsWhat · port 5000"
      />
      <CardBody>
        {loading && (
          <div className="space-y-3">
            <Skeleton className="h-8 w-1/3" />
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-5/6" />
            <div className="grid grid-cols-3 gap-2 pt-1">
              <Skeleton className="h-12" />
              <Skeleton className="h-12" />
              <Skeleton className="h-12" />
            </div>
          </div>
        )}

        {!loading && error && (
          <div className="rounded-lg border border-rose-400/30 bg-rose-500/10 p-3 text-sm text-rose-200 whitespace-pre-wrap">
            {error}
          </div>
        )}

        {!loading && !error && !profile && (
          <div className="text-sm text-[color:var(--color-muted)]">
            Submit the form to classify a subject along the K taxonomy.
          </div>
        )}

        {!loading && !error && profile && (
          <div className="space-y-3.5">
            <div>
              <div className="font-mono text-3xl font-bold tracking-tight text-white">
                {profile.classification_code}
              </div>
              <div className="text-sm text-ink-soft mt-0.5">
                {profile.classification_label}
              </div>
            </div>
            <div className="grid grid-cols-3 gap-2">
              <Pill label="Awareness" value={profile.awareness_failure_score} accent="#a5b4fc" />
              <Pill label="Intent" value={profile.intent_failure_score} accent="#a5b4fc" />
              <Pill label="Control" value={profile.control_failure_score} accent="#a5b4fc" />
            </div>
            <p className="text-sm text-ink-soft leading-relaxed pt-1">
              {profile.short_rationale}
            </p>
          </div>
        )}
      </CardBody>
    </Card>
  )
}
