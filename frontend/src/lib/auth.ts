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

export async function getCurrentUser() {
  const supabase = getSupabase();
  if (!supabase) return null;

  const {
    data: { user },
    error,
  } = await supabase.auth.getUser();

  if (error) {
    return null;
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

  // Fallback for demo navigation/browser contexts where the SSR cookie
  // storage has not been restored yet. The token was obtained directly from
  // Supabase during sign-in and is scoped to this browser tab.
  return readCachedToken();
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
