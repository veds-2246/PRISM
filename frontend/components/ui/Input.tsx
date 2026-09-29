import type { InputHTMLAttributes } from "react";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  hint?: string;
}

export function Input({
  label,
  error,
  hint,
  id,
  className = "",
  ...props
}: InputProps) {
  return (
    <div className="w-full">
      {label && (
        <label
          htmlFor={id}
          className="mb-1.5 block text-sm font-medium text-foreground"
        >
          {label}
        </label>
      )}

      <input
        id={id}
        className={`
          w-full rounded-lg border bg-surface px-3.5 py-2.5
          text-sm text-foreground
          placeholder:text-text-muted
          outline-none
          transition-colors
          focus:border-primary
          focus:ring-2
          focus:ring-primary/15
          disabled:cursor-not-allowed
          disabled:bg-surface-muted
          ${error ? "border-danger focus:border-danger focus:ring-danger/15" : "border-border"}
          ${className}
        `}
        {...props}
      />

      {error ? (
        <p className="mt-1.5 text-xs text-danger">{error}</p>
      ) : hint ? (
        <p className="mt-1.5 text-xs text-text-muted">{hint}</p>
      ) : null}
    </div>
  );
}
