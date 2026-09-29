const TOKEN_KEY = "prism_demo_token";
const USER_ID = "f9108bcd-758c-4187-899f-0be5c204d1d7";

export async function getCurrentUser() {
  if (typeof window === "undefined") return { id: USER_ID, email: "demo@prism-bis.in" };
  return { id: USER_ID, email: "demo@prism-bis.in", user_metadata: { full_name: "PRISM Demo User" } };
}

export async function getAccessToken() {
  if (typeof window === "undefined") return "demo-token";
  const token = window.sessionStorage.getItem(TOKEN_KEY) || "demo-token";
  window.sessionStorage.setItem(TOKEN_KEY, token);
  return token;
}

export function cacheAccessToken(token: string | null) {
  if (typeof window === "undefined") return;
  if (token) window.sessionStorage.setItem(TOKEN_KEY, token);
  else window.sessionStorage.removeItem(TOKEN_KEY);
}

export async function signOut() {
  if (typeof window !== "undefined") window.sessionStorage.removeItem(TOKEN_KEY);
}
