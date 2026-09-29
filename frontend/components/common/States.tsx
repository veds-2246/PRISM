import type { ReactNode } from "react";

export function LoadingState({ label = "Loading" }: { label?: string }) {
  return <div className="rounded-xl border border-border bg-surface p-10 text-center text-sm text-text-muted">{label}...</div>;
}

export function EmptyState({ title, action }: { title: string; action?: ReactNode }) {
  return <div className="rounded-xl border border-dashed border-border bg-surface p-10 text-center"><p className="text-sm text-text-muted">{title}</p>{action && <div className="mt-4">{action}</div>}</div>;
}

export function ErrorState({ message }: { message: string }) {
  return <div role="alert" className="rounded-xl border border-danger/20 bg-danger-bg p-4 text-sm text-danger">{message}</div>;
}
