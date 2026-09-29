"use client";

import Link from "next/link";
import { ArrowRight, FileText, Plus, Search, ShieldCheck } from "lucide-react";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/Button";
import { Card, CardContent, CardHeader } from "@/components/ui/Card";
import { EmptyState, ErrorState, LoadingState } from "@/components/common/States";
import { StatusBadge } from "@/components/common/StatusBadge";
import { api, type Analysis } from "@/src/lib/api";
import { getAccessToken } from "@/src/lib/auth";
import { getCurrentProfile, type UserProfile } from "@/src/lib/profile";

export default function DashboardPage() {
  const [analyses, setAnalyses] = useState<Analysis[]>([]);
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    async function loadWorkspace() {
      try {
        // Establish/restore the Supabase session before making protected API
        // requests. This is especially important for direct demo access to
        // /dashboard, where there was no prior /login navigation.
        await getAccessToken();
        const [rows, currentProfile] = await Promise.all([api.listAnalyses(), getCurrentProfile()]);
        setAnalyses(rows);
        setProfile(currentProfile);
      } catch (reason) {
        setError(reason instanceof Error ? reason.message : "Unable to load workspace.");
      } finally {
        setLoading(false);
      }
    }

    loadWorkspace();
  }, []);
  const completed = analyses.filter((item) => item.status === "completed").length;
  const review = analyses.filter((item) => item.status === "needs_review").length;
  if (loading) return <LoadingState label="Loading workspace" />;
  return (
    <div className="mx-auto max-w-7xl space-y-7">
      <div><p className="text-sm font-medium text-primary">Good day{profile?.full_name ? `, ${profile.full_name.split(" ")[0]}` : ""}</p><h1 className="mt-1 text-3xl font-semibold tracking-tight">Standards intelligence workspace</h1><p className="mt-2 text-sm text-text-muted">Decision-support recommendations grounded in Indian Standards records.</p></div>
      {error && <ErrorState message={error} />}
      <Card className="overflow-hidden border-primary/20"><CardContent className="flex flex-col justify-between gap-6 bg-primary p-6 text-white sm:flex-row sm:items-center"><div><div className="mb-3 flex h-10 w-10 items-center justify-center rounded-lg bg-white/10"><ShieldCheck className="h-5 w-5" /></div><h2 className="text-xl font-semibold">Start a new standards analysis</h2><p className="mt-1 max-w-xl text-sm text-white/70">Describe a product or procurement specification and receive traceable standard recommendations.</p></div><Link href="/dashboard/analysis"><Button variant="secondary"><Plus className="h-4 w-4" />New analysis</Button></Link></CardContent></Card>
      <div className="grid gap-4 sm:grid-cols-3"><Metric label="Total analyses" value={analyses.length} /><Metric label="Completed" value={completed} /><Metric label="Needs review" value={review} /></div>
      <Card><CardHeader><div className="flex items-center justify-between"><div><h2 className="font-semibold">Recent analyses</h2><p className="mt-1 text-xs text-text-muted">Your latest decision-support work</p></div><Link className="text-sm font-medium text-primary hover:underline" href="/dashboard/history">View history</Link></div></CardHeader><CardContent className="p-0">{analyses.length === 0 ? <div className="p-5"><EmptyState title="No analyses yet" action={<Link href="/dashboard/analysis"><Button><Plus className="h-4 w-4" />Start your first analysis</Button></Link>} /></div> : <div className="divide-y divide-border">{analyses.slice(0, 5).map((analysis) => <Link key={analysis.id} href={`/dashboard/analysis/${analysis.id}`} className="flex items-center justify-between gap-4 px-5 py-4 hover:bg-surface-muted"><div className="min-w-0"><p className="truncate text-sm font-medium">{analysis.product_name || analysis.query_text || "Untitled analysis"}</p><p className="mt-1 text-xs text-text-muted">{analysis.detected_language || "Language unavailable"} · {analysis.id.slice(0, 8)}</p></div><div className="flex items-center gap-3"><StatusBadge status={analysis.status} /><ArrowRight className="h-4 w-4 text-text-muted" /></div></Link>)}</div>}</CardContent></Card>
      <div className="grid gap-4 md:grid-cols-2"><Link href="/dashboard/standards"><Card className="h-full hover:border-primary/40"><CardContent className="flex items-center gap-4 p-5"><Search className="h-5 w-5 text-primary" /><div><p className="font-medium">Explore standards</p><p className="mt-1 text-xs text-text-muted">Search source-backed standard records.</p></div></CardContent></Card></Link><Link href="/dashboard/history"><Card className="h-full hover:border-primary/40"><CardContent className="flex items-center gap-4 p-5"><FileText className="h-5 w-5 text-primary" /><div><p className="font-medium">Review analysis history</p><p className="mt-1 text-xs text-text-muted">Open reports and follow review status.</p></div></CardContent></Card></Link></div>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: number }) {
  return <Card><CardContent className="p-5"><p className="text-xs text-text-muted">{label}</p><p className="mt-2 font-mono text-2xl font-semibold">{value || "No data yet"}</p></CardContent></Card>;
}
