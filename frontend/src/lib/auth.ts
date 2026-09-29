import { getSupabase } from "./supabase";

const ACCESS_TOKEN_KEY = "prism_supabase_access_token";

function readCachedToken() {
  if (typeof window === "undefined") return null;
  try {
    return window.sessionStorage.getItem(ACCESS_TOKEN_KEY);
  } catch {
    return null;
  }
}

function cacheToken(token: string | null) {
  if (typeof window === "undefined") return;
  try {
    if (token) {
      window.sessionStorage.setItem(ACCESS_TOKEN_KEY, token);
    } else {
      window.sessionStorage.removeItem(ACCESS_TOKEN_KEY);
    }
  } catch {
    // Session storage can be unavailable in restricted browser contexts.
  }
}

async function signInConfiguredDemo(supabase: NonNullable<ReturnType<typeof getSupabase>>) {
  const demoEmail = process.env.NEXT_PUBLIC_DEMO_EMAIL;
  const demoPassword = process.env.NEXT_PUBLIC_DEMO_PASSWORD;

  if (!demoEmail || !demoPassword) return null;

  const { data, error } = await supabase.auth.signInWithPassword({
    email: demoEmail,
    password: demoPassword,
  });

  if (error || !data.session?.access_token) return null;

  cacheToken(data.session.access_token);
  return data.session;
}

export async function getCurrentUser() {
  const supabase = getSupabase();
  if (!supabase) return null;

  const {
    data: { user },
    error,
  } = await supabase.auth.getUser();

  if (error || !user) {
    // The dashboard is intentionally demo-accessible. If there is no restored
    // browser session, establish the configured Supabase demo session so that
    // the protected FastAPI endpoints can still receive a real Bearer token.
    const demoSession = await signInConfiguredDemo(supabase);
    return demoSession?.user ?? null;
  }

  return user;
}

export async function getAccessToken() {
  const supabase = getSupabase();
  if (!supabase) return null;

  // First use the browser Supabase session. This is the source of truth.
  const {
    data: { session },
  } = await supabase.auth.getSession();

  if (session?.access_token) {
    cacheToken(session.access_token);
    return session.access_token;
  }

  // If the access token is missing/expired, let Supabase refresh it before
  // the API request is made. This is important immediately after login and
  // when a browser restores an existing session.
  const {
    data: { session: refreshedSession },
  } = await supabase.auth.refreshSession();

  if (refreshedSession?.access_token) {
    cacheToken(refreshedSession.access_token);
    return refreshedSession.access_token;
  }

  // Validate a cached token before reusing it. This prevents an expired token
  // from causing repeated 401 responses after a browser refresh.
  const cachedToken = readCachedToken();
  if (cachedToken) {
    const {
      data: { user },
      error,
    } = await supabase.auth.getUser(cachedToken);

    if (!error && user) {
      return cachedToken;
    }

    cacheToken(null);
  }

  // Demo deployments can be opened directly at /dashboard without visiting
  // /login. In that flow, sign in the configured Supabase demo account here so
  // every protected backend request still carries a genuine user access token.
  const demoSession = await signInConfiguredDemo(supabase);
  return demoSession?.access_token ?? null;
}

export function cacheAccessToken(token: string | null) {
  cacheToken(token);
}

export async function signOut() {
  const supabase = getSupabase();
  if (!supabase) return;

  const { error } = await supabase.auth.signOut();
  cacheToken(null);

  if (error) {
    throw error;
  }
}
