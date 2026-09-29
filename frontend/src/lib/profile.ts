export type AppRole = "admin" | "procurement_officer" | "auditor";

export interface UserProfile {
  id: string;
  organization_id: string | null;
  full_name: string;
  email: string;
  is_active: boolean;
  role: AppRole | null;
}

export async function getCurrentProfile(): Promise<UserProfile> {
  return {
    id: "f9108bcd-758c-4187-899f-0be5c204d1d7",
    organization_id: "demo-org",
    full_name: "PRISM Demo User",
    email: "demo@prism-bis.in",
    is_active: true,
    role: "admin",
  };
}
