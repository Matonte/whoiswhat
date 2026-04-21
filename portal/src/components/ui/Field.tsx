import {
  forwardRef,
  type InputHTMLAttributes,
  type LabelHTMLAttributes,
  type ReactNode,
  type SelectHTMLAttributes,
  type TextareaHTMLAttributes,
} from "react"
import { cn } from "@/lib/utils"

export function Label({
  className,
  ...props
}: LabelHTMLAttributes<HTMLLabelElement>) {
  return (
    <label
      className={cn(
        "block text-xs font-semibold uppercase tracking-[0.1em] text-[color:var(--color-muted)] mb-1.5",
        className
      )}
      {...props}
    />
  )
}

const fieldBase =
  "w-full rounded-lg bg-white/[0.04] border border-white/10 px-3.5 py-2.5 text-sm text-white placeholder:text-[color:var(--color-muted)]/60 outline-none transition focus:border-indigo-400/60 focus:bg-white/[0.06] focus:shadow-[0_0_0_3px_rgba(99,102,241,0.18)]"

export const Input = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement>>(
  ({ className, ...props }, ref) => (
    <input ref={ref} className={cn(fieldBase, "h-10", className)} {...props} />
  )
)
Input.displayName = "Input"

export const Textarea = forwardRef<
  HTMLTextAreaElement,
  TextareaHTMLAttributes<HTMLTextAreaElement>
>(({ className, ...props }, ref) => (
  <textarea
    ref={ref}
    className={cn(fieldBase, "min-h-[5.5rem] leading-relaxed resize-y", className)}
    {...props}
  />
))
Textarea.displayName = "Textarea"

export const Select = forwardRef<
  HTMLSelectElement,
  SelectHTMLAttributes<HTMLSelectElement> & { options: ReadonlyArray<{ value: string; label: string }> }
>(({ className, options, ...props }, ref) => (
  <select
    ref={ref}
    className={cn(
      fieldBase,
      "h-10 appearance-none bg-right bg-no-repeat pr-9",
      className
    )}
    style={{
      backgroundImage:
        "url(\"data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12' fill='none'><path d='M2.5 4.5L6 8L9.5 4.5' stroke='%237b88b8' stroke-width='1.5' stroke-linecap='round' stroke-linejoin='round'/></svg>\")",
      backgroundPosition: "right 0.85rem center",
    }}
    {...props}
  >
    {options.map((o) => (
      <option key={o.value} value={o.value} className="text-surface">
        {o.label}
      </option>
    ))}
  </select>
))
Select.displayName = "Select"

export function FieldGroup({
  label,
  htmlFor,
  hint,
  children,
  className,
}: {
  label: string
  htmlFor?: string
  hint?: string
  children: ReactNode
  className?: string
}) {
  return (
    <div className={cn("w-full", className)}>
      <Label htmlFor={htmlFor}>{label}</Label>
      {children}
      {hint && (
        <div className="mt-1 text-[0.72rem] text-[color:var(--color-muted)]">{hint}</div>
      )}
    </div>
  )
}
