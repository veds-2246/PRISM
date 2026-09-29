import type { ButtonHTMLAttributes, ReactNode } from "react";

type ButtonVariant =
  | "primary"
  | "secondary"
  | "outline"
  | "ghost"
  | "danger";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  children: ReactNode;
  loading?: boolean;
}

const variants: Record<ButtonVariant, string> = {
  primary:
    "bg-primary text-white hover:bg-primary-light focus-visible:ring-primary",
  secondary:
    "bg-surface-muted text-foreground hover:bg-border focus-visible:ring-primary",
  outline:
    "border border-border bg-surface text-foreground hover:bg-surface-muted focus-visible:ring-primary",
  ghost:
    "bg-transparent text-text-secondary hover:bg-surface-muted hover:text-foreground focus-visible:ring-primary",
  danger:
    "bg-danger text-white hover:bg-red-800 focus-visible:ring-danger",
};

export function Button({
  variant = "primary",
  children,
  loading = false,
  disabled,
  className = "",
  ...props
}: ButtonProps) {
  return (
    <button
      disabled={disabled || loading}
      className={`
        inline-flex items-center justify-center gap-2
        rounded-lg px-4 py-2.5
        text-sm font-medium
        transition-colors duration-150
        focus-visible:outline-none
        focus-visible:ring-2
        focus-visible:ring-offset-2
        disabled:cursor-not-allowed
        disabled:opacity-50
        ${variants[variant]}
        ${className}
      `}
      {...props}
    >
      {loading ? (
        <>
          <span
            className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent"
            aria-hidden="true"
          />
          <span>Processing...</span>
        </>
      ) : (
        children
      )}
    </button>
  );
}
