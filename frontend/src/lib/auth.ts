import { getSupabase } from "./supabase";

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

  // Read the persisted browser session first.
  const {
    data: { session },
  } = await supabase.auth.getSession();

  if (session?.access_token) {
    return session.access_token;
  }

  // If the access token is missing/expired, let Supabase refresh it before
  // the API request is made. This is especially important immediately after
  // demo login and after a browser has restored an existing session.
  const {
    data: { session: refreshedSession },
  } = await supabase.auth.refreshSession();

  return refreshedSession?.access_token ?? null;
}

export async function signOut() {
  const supabase = getSupabase();
  if (!supabase) return;

  const { error } = await supabase.auth.signOut();

  if (error) {
    throw error;
  }
}
