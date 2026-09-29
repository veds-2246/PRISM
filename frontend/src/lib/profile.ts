import { getSupabase } from "./supabase";

export type AppRole =
  | "admin"
  | "procurement_officer"
  | "auditor";

export interface UserProfile {
  id: string;
  organization_id: string | null;
  full_name: string;
  email: string;
  is_active: boolean;
  role: AppRole | null;
}

export async function getCurrentProfile(): Promise<UserProfile | null> {
  const supabase = getSupabase();
  if (!supabase) return null;

  const {
    data: { user },
    error: authError,
  } = await supabase.auth.getUser();

  if (authError || !user) {
    return null;
  }

  const { data: profile, error: profileError } = await supabase
    .from("profiles")
    .select("id, organization_id, full_name, email, is_active")
    .eq("id", user.id)
    .single();

  if (profileError || !profile) {
    return null;
  }

  const { data: roleData } = await supabase
    .from("profile_roles")
    .select("role")
    .eq("profile_id", user.id)
    .limit(1)
    .maybeSingle();

  return {
    ...profile,
    role: (roleData?.role as AppRole | undefined) ?? null,
  };
}
