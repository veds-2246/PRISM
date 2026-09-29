import { redirect } from "next/navigation";
import { createSupabaseServerClient } from "@/src/lib/supabase-server";

export default async function Home() {
  const supabase = await createSupabaseServerClient();
  const { data: { user } } = await supabase.auth.getUser();
  redirect(user ? "/dashboard" : "/login");
}
