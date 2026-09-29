import { Badge } from "@/components/ui/Badge";

export function StatusBadge({ status }: { status: string }) {
  const variant = status === "completed" || status === "accepted" ? "success" : status === "failed" || status === "rejected" ? "danger" : status === "processing" || status === "needs_review" ? "warning" : "info";
  return <Badge variant={variant}>{status.replaceAll("_", " ")}</Badge>;
}

export function ScoreIndicator({ label, value }: { label: string; value: number }) {
  return <div><div className="flex justify-between text-xs text-text-muted"><span>{label}</span><span className="font-mono text-foreground">{Math.round(value * 100)}%</span></div><div className="mt-1 h-1.5 rounded-full bg-surface-muted"><div className="h-1.5 rounded-full bg-primary" style={{ width: `${Math.max(0, Math.min(100, value * 100))}%` }} /></div></div>;
}
