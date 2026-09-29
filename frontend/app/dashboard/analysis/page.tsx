"use client";

import { useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { FileUp, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Card, CardContent, CardHeader } from "@/components/ui/Card";
import { ErrorState } from "@/components/common/States";
import { api } from "@/src/lib/api";

export default function NewAnalysisPage() {
  const router = useRouter();
  const fileRef = useRef<HTMLInputElement>(null);
  const [query, setQuery] = useState("");
  const [product, setProduct] = useState("");
  const [specifications, setSpecifications] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  function chooseFile(candidate: File | undefined) {
    if (!candidate) return;
    if (candidate.type !== "application/pdf" && !candidate.name.toLowerCase().endsWith(".pdf")) {
      setError("Only PDF files are supported for document extraction.");
      return;
    }
    setError("");
    setFile(candidate);
  }
  async function submit() {
    if (!query.trim() && !file) { setError("Enter a specification or choose a document."); return; }
    setLoading(true); setError("");
    try {
      const analysis = await api.createAnalysis({ query_text: query.trim() || file?.name || "Uploaded procurement document", product_name: product || undefined, technical_specifications: specifications || undefined, defer_processing: Boolean(file) });
      if (file) await api.uploadDocument(analysis.id, file);
      router.push(`/dashboard/analysis/${analysis.id}`);
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Analysis could not be created."); } finally { setLoading(false); }
  }
  return <div className="mx-auto max-w-4xl space-y-6"><div><p className="text-sm font-medium text-primary">Workspace</p><h1 className="mt-1 text-3xl font-semibold">New standards analysis</h1><p className="mt-2 text-sm text-text-muted">Provide the product context and technical requirements you want the system to evaluate.</p></div><Card><CardHeader><h2 className="font-semibold">Specification input</h2></CardHeader><CardContent className="space-y-5 p-5"><label className="block"><span className="mb-1.5 block text-sm font-medium">Product or procurement description</span><textarea value={query} onChange={(e) => setQuery(e.target.value)} rows={7} placeholder="Describe the product, material or technical specification..." className="w-full resize-y rounded-lg border border-border bg-surface px-3.5 py-3 text-sm outline-none focus:border-primary focus:ring-2 focus:ring-primary/15" /></label><label className="block"><span className="mb-1.5 block text-sm font-medium">Product name <span className="font-normal text-text-muted">(optional)</span></span><input value={product} onChange={(e) => setProduct(e.target.value)} className="w-full rounded-lg border border-border px-3.5 py-2.5 text-sm outline-none focus:border-primary" /></label><label className="block"><span className="mb-1.5 block text-sm font-medium">Technical specifications <span className="font-normal text-text-muted">(optional)</span></span><textarea value={specifications} onChange={(e) => setSpecifications(e.target.value)} rows={4} className="w-full resize-y rounded-lg border border-border bg-surface px-3.5 py-3 text-sm outline-none focus:border-primary" /></label><div onClick={() => fileRef.current?.click()} onDragOver={(e) => e.preventDefault()} onDrop={(e) => { e.preventDefault(); chooseFile(e.dataTransfer.files[0]); }} className="cursor-pointer rounded-xl border border-dashed border-border-strong bg-surface-muted p-6 text-center hover:border-primary"><FileUp className="mx-auto h-6 w-6 text-primary" /><p className="mt-2 text-sm font-medium">{file ? file.name : "Drop a PDF here or browse"}</p>{file && <p className="mt-1 text-xs text-text-muted">{formatFileSize(file.size)}</p>}<p className="mt-1 text-xs text-text-muted">Supported: PDF · max size configured by backend</p><input ref={fileRef} type="file" accept=".pdf,application/pdf" className="hidden" onChange={(e) => chooseFile(e.target.files?.[0])} /></div>{error && <ErrorState message={error} />}<div className="flex justify-end"><Button onClick={submit} loading={loading}><Sparkles className="h-4 w-4" />{loading ? "Uploading and processing..." : "Analyze specifications"}</Button></div></CardContent></Card></div>;
}

function formatFileSize(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
