"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

const NAV_ITEMS = [
  { href: "/", label: "博客" },
  { href: "/news", label: "资讯" },
  { href: "/about", label: "关于" },
];

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

interface MeResponse {
  user: {
    role: string;
  } | null;
}

export default function Navbar() {
  const pathname = usePathname();
  const [userRole, setUserRole] = useState<string | null>(null);
  const [authChecked, setAuthChecked] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function loadMe() {
      try {
        const res = await fetch(`${API_BASE}/auth/me`, {
          credentials: "include",
          cache: "no-store",
        });
        if (!res.ok) return;

        const data = (await res.json()) as MeResponse;
        if (!cancelled) {
          setUserRole(data.user?.role ?? null);
        }
      } finally {
        if (!cancelled) {
          setAuthChecked(true);
        }
      }
    }

    void loadMe();
    return () => {
      cancelled = true;
    };
  }, []);

  const authItems = useMemo(() => {
    if (!authChecked || !userRole) {
      return [{ href: "/login", label: "登录" }];
    }
    if (userRole === "admin") {
      return [{ href: "/admin", label: "后台" }];
    }
    return [];
  }, [authChecked, userRole]);

  const visibleItems = [...NAV_ITEMS, ...authItems];

  function isActive(href: string) {
    if (href === "/") return pathname === "/";
    return pathname.startsWith(href);
  }

  return (
    <nav className="border-b border-foreground/10">
      <div className="mx-auto flex max-w-3xl items-center justify-between px-4 py-3">
        <Link href="/" className="text-lg font-bold">
          {process.env.NEXT_PUBLIC_SITE_NAME || "Cici Blog"}
        </Link>

        <div className="flex items-center gap-6">
          {visibleItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={`text-sm transition-colors ${
                isActive(item.href)
                  ? "font-medium text-foreground"
                  : "text-foreground/50 hover:text-foreground"
              }`}
            >
              {item.label}
            </Link>
          ))}
        </div>
      </div>
    </nav>
  );
}
