import { useState, type FormEvent } from "react"
import { Sparkles } from "lucide-react"
import { Button } from "@/components/ui/Button"
import { FieldGroup, Input, Select, Textarea } from "@/components/ui/Field"
import { Spinner } from "@/components/ui/Misc"
import type { AdviseRequest, RiskLevel } from "@/types"

const SETTINGS = [
  "work",
  "social",
  "family",
  "negotiation",
  "first-date",
  "conflict",
  "interview",
  "other",
] as const

const STAKES: RiskLevel[] = ["low", "medium", "high"]

interface Props {
  loading: boolean
  onSubmit(req: AdviseRequest): void
}

export function SubjectForm({ loading, onSubmit }: Props) {
  const [name, setName] = useState("")
  const [source, setSource] = useState("")
  const [notes, setNotes] = useState("")
  const [setting, setSetting] = useState<string>("work")
  const [stakes, setStakes] = useState<RiskLevel>("medium")
  const [yourRole, setYourRole] = useState("")
  const [goals, setGoals] = useState("")

  const submit = (e: FormEvent) => {
    e.preventDefault()
    const trimmed = name.trim()
    if (!trimmed) return
    onSubmit({
      subject_name: trimmed,
      source_hint: source.trim() || null,
      notes: notes.trim() || null,
      context: {
        setting,
        stakes,
        your_role: yourRole.trim() || null,
        goals: goals.trim() || null,
      },
    })
  }

  return (
    <form onSubmit={submit} className="space-y-5">
      <div className="grid gap-4 md:grid-cols-2">
        <FieldGroup label="Subject name" htmlFor="subject_name">
          <Input
            id="subject_name"
            autoComplete="off"
            placeholder="e.g. Walter White"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
          />
        </FieldGroup>
        <FieldGroup label="Source / context hint" htmlFor="source_hint">
          <Input
            id="source_hint"
            autoComplete="off"
            placeholder="Breaking Bad / colleague / invented"
            value={source}
            onChange={(e) => setSource(e.target.value)}
          />
        </FieldGroup>
      </div>
      <FieldGroup label="Notes about the subject" htmlFor="notes" hint="Optional. Grounds both classifiers.">
        <Textarea
          id="notes"
          placeholder="Anything you know about them that's relevant."
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
        />
      </FieldGroup>

      <div className="pt-2">
        <div className="text-xs font-semibold uppercase tracking-[0.12em] text-[color:var(--color-muted)] mb-3">
          Meeting context
        </div>
        <div className="grid gap-4 md:grid-cols-2">
          <FieldGroup label="Setting" htmlFor="setting">
            <Select
              id="setting"
              value={setting}
              onChange={(e) => setSetting(e.target.value)}
              options={SETTINGS.map((s) => ({ value: s, label: s }))}
            />
          </FieldGroup>
          <FieldGroup label="Stakes" htmlFor="stakes">
            <Select
              id="stakes"
              value={stakes}
              onChange={(e) => setStakes(e.target.value as RiskLevel)}
              options={STAKES.map((s) => ({ value: s, label: s }))}
            />
          </FieldGroup>
        </div>
        <div className="mt-4">
          <FieldGroup label="Your role" htmlFor="your_role">
            <Input
              id="your_role"
              placeholder="project manager, prospective buyer, ex-colleague…"
              value={yourRole}
              onChange={(e) => setYourRole(e.target.value)}
            />
          </FieldGroup>
        </div>
        <div className="mt-4">
          <FieldGroup label="Your goals for the meeting" htmlFor="goals">
            <Textarea
              id="goals"
              placeholder="What do you want out of the meeting?"
              value={goals}
              onChange={(e) => setGoals(e.target.value)}
            />
          </FieldGroup>
        </div>
      </div>

      <Button type="submit" size="lg" disabled={loading || !name.trim()} className="w-full">
        {loading ? <Spinner className="h-4 w-4" /> : <Sparkles className="h-4 w-4" />}
        {loading ? "Consulting models…" : "Classify + get meeting advice"}
      </Button>
    </form>
  )
}
