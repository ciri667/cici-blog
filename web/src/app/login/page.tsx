"use client";

import { FormEvent, useState } from "react";
import { apiFetch, ApiError } from "@/lib/api";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const data = await apiFetch<{ role: string }>("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });

      if (data.role === "admin") {
        window.location.href = "/admin";
      } else {
        window.location.href = "/";
      }
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("登录失败，请稍后重试");
      }
    } finally {
      setLoading(false);
    }
  }

  async function handleOAuth(provider: "google" | "github") {
    try {
      const data = await apiFetch<{ url: string }>(
        `/auth/oauth/${provider}/url`,
      );
      window.location.href = data.url;
    } catch {
      setError(`无法启动 ${provider === "google" ? "Google" : "GitHub"} 登录`);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="w-full max-w-sm space-y-6">
        <div className="text-center">
          <h1 className="text-2xl font-bold tracking-tight">登录</h1>
          <p className="mt-1 text-sm text-foreground/60">
            登录以管理博客内容
          </p>
        </div>

        {error && (
          <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-800 dark:bg-red-950 dark:text-red-300">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label
              htmlFor="email"
              className="block text-sm font-medium text-foreground/80"
            >
              邮箱
            </label>
            <input
              id="email"
              type="email"
              required
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="mt-1 block w-full rounded-md border border-foreground/20 bg-background px-3 py-2 text-sm shadow-sm placeholder:text-foreground/40 focus:border-foreground/50 focus:outline-none focus:ring-1 focus:ring-foreground/50"
              placeholder="you@example.com"
            />
          </div>

          <div>
            <label
              htmlFor="password"
              className="block text-sm font-medium text-foreground/80"
            >
              密码
            </label>
            <input
              id="password"
              type="password"
              required
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="mt-1 block w-full rounded-md border border-foreground/20 bg-background px-3 py-2 text-sm shadow-sm placeholder:text-foreground/40 focus:border-foreground/50 focus:outline-none focus:ring-1 focus:ring-foreground/50"
              placeholder="输入密码"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-md bg-foreground px-4 py-2 text-sm font-medium text-background transition-opacity hover:opacity-90 disabled:opacity-50"
          >
            {loading ? "登录中..." : "登录"}
          </button>
        </form>

        <div className="relative">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-foreground/10" />
          </div>
          <div className="relative flex justify-center text-xs">
            <span className="bg-background px-2 text-foreground/40">
              或使用第三方账号
            </span>
          </div>
        </div>

        <div className="space-y-3">
          <button
            type="button"
            onClick={() => handleOAuth("google")}
            className="flex w-full items-center justify-center gap-3 rounded-md border border-foreground/20 bg-background px-4 py-2 text-sm font-medium transition-colors hover:bg-foreground/5"
          >
            <svg className="h-5 w-5" viewBox="0 0 24 24">
              <path
                d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 01-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z"
                fill="#4285F4"
              />
              <path
                d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                fill="#34A853"
              />
              <path
                d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                fill="#FBBC05"
              />
              <path
                d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                fill="#EA4335"
              />
            </svg>
            使用 Google 账号登录
          </button>

          <button
            type="button"
            onClick={() => handleOAuth("github")}
            className="flex w-full items-center justify-center gap-3 rounded-md border border-foreground/20 bg-background px-4 py-2 text-sm font-medium transition-colors hover:bg-foreground/5"
          >
            <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" />
            </svg>
            使用 GitHub 账号登录
          </button>
        </div>
      </div>
    </div>
  );
}
