"use client";

import { useEffect, useState } from "react";
import { apiFetch, ApiError } from "@/lib/api";

export default function GoogleCallbackPage() {
  const [error, setError] = useState("");

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const code = params.get("code");
    const authError = params.get("error");

    if (authError) {
      setError("授权已取消");
      return;
    }

    if (!code) {
      setError("缺少授权码");
      return;
    }

    apiFetch<{ role: string }>(`/auth/oauth/google/callback?code=${encodeURIComponent(code)}`, {
      method: "POST",
    })
      .then((data) => {
        window.location.href = data.role === "admin" ? "/admin" : "/";
      })
      .catch((err) => {
        if (err instanceof ApiError) {
          setError(err.message);
        } else {
          setError("Google 登录失败，请稍后重试");
        }
      });
  }, []);

  if (error) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background px-4">
        <div className="w-full max-w-sm space-y-4 text-center">
          <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-800 dark:bg-red-950 dark:text-red-300">
            {error}
          </div>
          <a
            href="/login"
            className="inline-block text-sm text-foreground/60 underline hover:text-foreground"
          >
            返回登录
          </a>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-background">
      <p className="text-sm text-foreground/60">正在完成 Google 登录...</p>
    </div>
  );
}
