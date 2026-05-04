import { cva, type VariantProps } from "class-variance-authority"
import { forwardRef, type ButtonHTMLAttributes } from "react"
import { cn } from "@/lib/utils"

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap transition-all disabled:pointer-events-none disabled:opacity-45 cursor-pointer rounded-none focus-visible:outline focus-visible:outline-2 focus-visible:outline-[color:var(--accent-dim)] focus-visible:outline-offset-2",
  {
    variants: {
      variant: {
        primary:
          "portal-btn-primary px-[18px] py-2.5 font-[family-name:var(--font-display)]",
        secondary:
          "portal-btn-secondary px-[18px] py-2.5 font-[family-name:var(--font-display)]",
        ghost:
          "bg-transparent text-[color:var(--fg-muted)] border border-transparent hover:text-[color:var(--accent)] hover:bg-[rgba(79,255,196,0.06)] px-3 py-2 font-[family-name:var(--font-mono)] text-[0.72rem] uppercase tracking-[0.08em]",
        danger:
          "border border-[color:var(--danger-muted)] bg-[rgba(140,53,64,0.35)] text-[color:var(--danger)] hover:bg-[rgba(255,107,122,0.18)] px-[18px] py-2.5 font-[family-name:var(--font-display)] text-[0.72rem] uppercase tracking-[0.12em]",
      },
      size: {
        sm: "min-h-8 px-3 py-1.5 text-[0.68rem]",
        md: "min-h-10",
        lg: "min-h-11 px-6 py-3 text-[0.78rem]",
      },
    },
    defaultVariants: { variant: "primary", size: "md" },
  }
)

export type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> &
  VariantProps<typeof buttonVariants>

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, ...props }, ref) => (
    <button ref={ref} className={cn(buttonVariants({ variant, size }), className)} {...props} />
  )
)
Button.displayName = "Button"
