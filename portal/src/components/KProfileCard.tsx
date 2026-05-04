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
        accent="var(--color-contact-advisor)"
        title={
          <span className="inline-flex items-center gap-2">
            <Tags className="h-3.5 w-3.5 text-[color:var(--accent)]" />
            K Taxonomy
          </span>
        }
        subtitle="Contact Advisor · port 5000"
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
          <div className="rounded-[var(--radius-inner)] border border-[color:var(--danger-muted)] bg-[rgba(140,53,64,0.2)] p-3 text-sm text-[color:var(--danger)] whitespace-pre-wrap font-[family-name:var(--font-mono)]">
            {error}
          </div>
        )}

        {!loading && !error && !profile && (
          <div className="text-sm text-[color:var(--fg-dim)]">
            Submit the form to classify a subject along the K taxonomy.
          </div>
        )}

        {!loading && !error && profile && (
          <div className="space-y-3.5">
            <div>
              <div className="font-[family-name:var(--font-mono)] text-3xl font-bold tracking-tight text-[color:var(--accent)]">
                {profile.classification_code}
              </div>
              <div className="text-sm text-[color:var(--fg-muted)] mt-0.5">
                {profile.classification_label}
              </div>
            </div>
            <div className="grid grid-cols-3 gap-2">
              <Pill label="Awareness" value={profile.awareness_failure_score} accent="var(--accent-2)" />
              <Pill label="Intent" value={profile.intent_failure_score} accent="var(--accent-2)" />
              <Pill label="Control" value={profile.control_failure_score} accent="var(--accent-2)" />
            </div>
            <p className="text-sm text-[color:var(--fg-muted)] leading-relaxed pt-1">
              {profile.short_rationale}
            </p>
          </div>
        )}
      </CardBody>
    </Card>
  )
}
