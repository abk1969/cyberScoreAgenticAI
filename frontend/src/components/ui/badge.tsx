import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-blue focus:ring-offset-2",
  {
    variants: {
      variant: {
        default: "border-transparent bg-navy text-white",
        secondary: "border-transparent bg-bg text-text",
        outline: "border-border text-text",
        "grade-a": "border-transparent bg-score-a text-white",
        "grade-b": "border-transparent bg-score-b text-white",
        "grade-c": "border-transparent bg-score-c text-white",
        "grade-d": "border-transparent bg-score-d text-white",
        "grade-f": "border-transparent bg-score-f text-white",
        critical: "border-transparent bg-score-f text-white",
        high: "border-transparent bg-score-d text-white",
        medium: "border-transparent bg-score-c text-white",
        low: "border-transparent bg-score-b text-white",
        info: "border-transparent bg-muted text-white",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
);

interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return <div className={cn(badgeVariants({ variant }), className)} {...props} />;
}

function GradeBadge({ grade }: { grade: string }) {
  const variant = `grade-${grade.toLowerCase()}` as BadgeProps["variant"];
  return <Badge variant={variant}>{grade}</Badge>;
}

export { Badge, GradeBadge, badgeVariants };
