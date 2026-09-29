"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { Eye, EyeOff, ShieldCheck } from "lucide-react";
import { cacheAccessToken } from "@/src/lib/auth";
import { getSupabase } from "@/src/lib/supabase";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";

export default function LoginPage() {
  const router = useRouter();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [demoLoading, setDemoLoading] = useState(false);

  async function signIn(emailAddress: string, passwordValue: string) {
    const supabase = getSupabase();

    if (!supabase) {
      throw new Error("Supabase is unavailable in this environment.");
    }

    const { data, error: authError } = await supabase.auth.signInWithPassword({
      email: emailAddress,
      password: passwordValue,
    });

    if (authError) {
      throw authError;
    }

    // The API requires this exact Supabase access token as a Bearer token.
    // Cache it for the current browser tab as a fallback while the SSR cookie
    // session is being restored after navigation.
    if (data.session?.access_token) {
      cacheAccessToken(data.session.access_token);
      return;
    }

    const {
      data: { session },
    } = await supabase.auth.getSession();

    if (!session?.access_token) {
      throw new Error("Sign-in succeeded but no Supabase session was created.");
    }

    cacheAccessToken(session.access_token);
  }

  async function handleLogin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    setError("");
    setLoading(true);

    try {
      await signIn(email, password);
      router.push("/dashboard");
      router.refresh();
    } catch (authError) {
      setError(authError instanceof Error ? authError.message : "Unable to sign in.");
      setLoading(false);
    }
  }

  async function handleDemoLogin() {
    setError("");
    setDemoLoading(true);

    const demoEmail = process.env.NEXT_PUBLIC_DEMO_EMAIL;
    const demoPassword = process.env.NEXT_PUBLIC_DEMO_PASSWORD;

    if (!demoEmail || !demoPassword) {
      setError("Demo access is not configured yet.");
      setDemoLoading(false);
      return;
    }

    try {
      await signIn(demoEmail, demoPassword);
      router.push("/dashboard");
      router.refresh();
    } catch (authError) {
      setError(authError instanceof Error ? authError.message : "Demo access is unavailable.");
      setDemoLoading(false);
    }
  }

  return (
    <main className="flex min-h-screen bg-background">
      <section className="hidden w-1/2 flex-col justify-between bg-primary p-10 text-white lg:flex">
        <div>
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-white/10">
              <ShieldCheck className="h-6 w-6" />
            </div>
            <div>
              <p className="text-base font-semibold">BIS Standards</p>
              <p className="text-sm text-white/65">Intelligence</p>
            </div>
          </div>
        </div>

        <div className="max-w-lg">
          <p className="mb-4 text-sm font-medium uppercase tracking-widest text-accent-light">
            Smart Procurement Decision Support
          </p>
          <h1 className="text-4xl font-semibold leading-tight">
            Identify the Indian Standards that matter to your procurement
            specifications.
          </h1>
          <p className="mt-5 max-w-md text-base leading-7 text-white/70">
            Analyze product descriptions and technical requirements to discover
            applicable standards with traceable recommendations and evidence.
          </p>
        </div>

        <p className="text-xs text-white/45">Department of Consumer Affairs</p>
      </section>

      <section className="flex w-full items-center justify-center px-6 py-10 lg:w-1/2">
        <div className="w-full max-w-md">
          <div className="mb-10 flex items-center gap-3 lg:hidden">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary text-white">
              <ShieldCheck className="h-5 w-5" />
            </div>
            <div>
              <p className="text-sm font-semibold text-foreground">BIS Standards</p>
              <p className="text-xs text-text-muted">Intelligence</p>
            </div>
          </div>

          <div className="mb-8">
            <p className="mb-2 text-sm font-medium text-primary">Welcome back</p>
            <h2 className="text-3xl font-semibold tracking-tight text-foreground">Sign in</h2>
            <p className="mt-2 text-sm leading-6 text-text-muted">
              Sign in to access the standards recommendation workspace.
            </p>
          </div>

          <form onSubmit={handleLogin} className="space-y-5">
            <Input
              id="email"
              label="Email address"
              type="email"
              placeholder="you@example.com"
              autoComplete="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              required
            />

            <div className="relative">
              <Input
                id="password"
                label="Password"
                type={showPassword ? "text" : "password"}
                placeholder="Enter your password"
                autoComplete="current-password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                className="pr-11"
                required
              />
              <button
                type="button"
                onClick={() => setShowPassword((value) => !value)}
                className="absolute right-3 top-[34px] flex h-8 w-8 items-center justify-center rounded-md text-text-muted hover:bg-surface-muted hover:text-foreground"
                aria-label={showPassword ? "Hide password" : "Show password"}
              >
                {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>

            {error && (
              <div role="alert" className="rounded-lg border border-danger/20 bg-danger-bg px-4 py-3 text-sm text-danger">
                {error}
              </div>
            )}

            <Button type="submit" loading={loading} className="w-full">Sign in</Button>
          </form>

          <div className="my-6 flex items-center gap-3">
            <div className="h-px flex-1 bg-border" />
            <span className="text-xs text-text-muted">or</span>
            <div className="h-px flex-1 bg-border" />
          </div>

          <Button
            type="button"
            variant="secondary"
            loading={demoLoading}
            onClick={handleDemoLogin}
            className="w-full"
          >
            Continue as Demo
          </Button>

          <p className="mt-8 text-center text-xs leading-5 text-text-muted">
            Demo mode provides access to the decision-support workspace using a
            dedicated demo account. Authorized users can sign in above.
          </p>
        </div>
      </section>
    </main>
  );
}
