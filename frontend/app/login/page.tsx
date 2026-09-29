"use client";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { Eye, EyeOff, ShieldCheck } from "lucide-react";
import { cacheAccessToken } from "@/src/lib/auth";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";

export default function LoginPage() {
  const router = useRouter();
  const [email,setEmail]=useState("demo@prism-bis.in");
  const [password,setPassword]=useState("demo123");
  const [showPassword,setShowPassword]=useState(false);
  const [error,setError]=useState("");
  const [loading,setLoading]=useState(false);

  function enterWorkspace(emailAddress:string) {
    if (!emailAddress.trim()) { setError("Enter an email address."); return; }
    cacheAccessToken("demo-token");
    router.push("/dashboard");
  }
  function handleLogin(event:FormEvent<HTMLFormElement>) { event.preventDefault(); setError(""); setLoading(true); setTimeout(()=>{enterWorkspace(email);setLoading(false)},250); }
  function handleDemoLogin() { setError(""); setLoading(true); setTimeout(()=>{enterWorkspace("demo@prism-bis.in");setLoading(false)},200); }

  return <main className="flex min-h-screen bg-background">
    <section className="hidden w-1/2 flex-col justify-between bg-primary p-10 text-white lg:flex">
      <div className="flex items-center gap-3"><div className="flex h-11 w-11 items-center justify-center rounded-xl bg-white/10"><ShieldCheck className="h-6 w-6"/></div><div><p className="text-base font-semibold">BIS Standards</p><p className="text-sm text-white/65">Intelligence</p></div></div>
      <div className="max-w-lg"><p className="mb-4 text-sm font-medium uppercase tracking-widest text-accent-light">Smart Procurement Decision Support</p><h1 className="text-4xl font-semibold leading-tight">Identify the Indian Standards that matter to your procurement specifications.</h1><p className="mt-5 max-w-md text-base leading-7 text-white/70">Analyze product descriptions and technical requirements to discover applicable standards with traceable recommendations and evidence.</p></div>
      <p className="text-xs text-white/45">Department of Consumer Affairs</p>
    </section>
    <section className="flex w-full items-center justify-center px-6 py-10 lg:w-1/2"><div className="w-full max-w-md">
      <div className="mb-10 flex items-center gap-3 lg:hidden"><div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary text-white"><ShieldCheck className="h-5 w-5"/></div><div><p className="text-sm font-semibold">BIS Standards</p><p className="text-xs text-text-muted">Intelligence</p></div></div>
      <div className="mb-8"><p className="mb-2 text-sm font-medium text-primary">Demo workspace</p><h2 className="text-3xl font-semibold tracking-tight">Sign in</h2><p className="mt-2 text-sm leading-6 text-text-muted">This presentation build runs entirely in the browser. No backend or API is required.</p></div>
      <form onSubmit={handleLogin} className="space-y-5"><Input id="email" label="Email address" type="email" value={email} onChange={e=>setEmail(e.target.value)} required/><div className="relative"><Input id="password" label="Password" type={showPassword?"text":"password"} value={password} onChange={e=>setPassword(e.target.value)} className="pr-11" required/><button type="button" onClick={()=>setShowPassword(x=>!x)} className="absolute right-3 top-[34px] flex h-8 w-8 items-center justify-center rounded-md text-text-muted hover:bg-surface-muted">{showPassword?<EyeOff className="h-4 w-4"/>:<Eye className="h-4 w-4"/>}</button></div>{error&&<div role="alert" className="rounded-lg border border-danger/20 bg-danger-bg px-4 py-3 text-sm text-danger">{error}</div>}<Button type="submit" loading={loading} className="w-full">Sign in</Button></form>
      <div className="my-6 flex items-center gap-3"><div className="h-px flex-1 bg-border"/><span className="text-xs text-text-muted">or</span><div className="h-px flex-1 bg-border"/></div>
      <Button type="button" variant="secondary" onClick={handleDemoLogin} loading={loading} className="w-full">Continue as Demo</Button>
      <div className="mt-6 rounded-lg bg-surface-muted p-4 text-xs text-text-muted"><p className="font-semibold text-foreground">Demo account</p><p className="mt-1">demo@prism-bis.in · demo123</p><p className="mt-2">Role: Administrator · Local browser demo</p></div>
    </div></section>
  </main>;
}
