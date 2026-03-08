import type { ReactNode } from "react";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

interface MeResponse {
  user: {
    role: string;
  } | null;
}

async function getMe(): Promise<MeResponse | null> {
  const cookieStore = await cookies();
  const token = cookieStore.get("access_token")?.value;

  if (!token) {
    return null;
  }

  const res = await fetch(`${API_BASE}/auth/me`, {
    headers: {
      cookie: `access_token=${encodeURIComponent(token)}`,
    },
    cache: "no-store",
  });

  if (!res.ok) {
    return null;
  }

  return (await res.json()) as MeResponse;
}

export default async function AdminLayout({
  children,
}: {
  children: ReactNode;
}) {
  const me = await getMe();
  if (me?.user?.role !== "admin") {
    redirect("/login");
  }

  return <>{children}</>;
}
