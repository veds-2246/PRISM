"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { Card, CardContent } from "@/components/ui/Card";
import { EmptyState, ErrorState, LoadingState } from "@/components/common/States";
import { StatusBadge } from "@/components/common/StatusBadge";
import { api, type Analysis } from "@/src/lib/api";

export default function ReviewsPage() {
  const [rows, setRows] = useState<Analysis[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  useEffect(() => {
    api.listAnalyses()
      .then((data) => setRows(data.filter((item) => item.status === "needs_review")))
      .catch((reason: Error) => setError(reason.message))
      .finally(() => setLoading(false));
  }, []);
  return <div className="mx-auto max-w-6xl space-y-6"><div><p className="text-sm font-medium text-primary">Governance</p><h1 className="mt-1 text-3xl font-semibold">Reviews</h1><p className="mt-2 text-sm text-text-muted">Open analyses flagged for further human review.</p></div>{error ? <ErrorState message={error} /> : loading ? <LoadingState label="Loading reviews" /> : rows.length ? <div className="space-y-3">{rows.map((row) => <Link key={row.id} href={`/dashboard/analysis/${row.id}`}><Card className="hover:border-primary/40"><CardContent className="flex items-center justify-between gap-4 p-5"><div><p className="font-medium">{row.product_name || row.query_text || "Untitled analysis"}</p><p className="mt-1 text-xs text-text-muted">{row.id}</p></div><StatusBadge status={row.status} /></CardContent></Card></Link>)}</div> : <EmptyState title="No analyses currently need review" />}</div>;
}
