"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiFetch, ApiError } from "@/lib/api";
import type { NewsListItem } from "@/lib/types";

export default function AdminNewsPage() {
  const [articles, setArticles] = useState<NewsListItem[]>([]);
  const [filter, setFilter] = useState<"all" | "pending" | "published">("all");
  const [loading, setLoading] = useState(true);

  async function loadArticles() {
    setLoading(true);
    try {
      const params = filter === "all" ? "" : `?status=${filter}`;
      const data = await apiFetch<{ items: NewsListItem[] }>(
        `/admin/news${params}`,
      );
      setArticles(data.items);
    } catch {
      setArticles([]);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadArticles();
  }, [filter]);

  async function handlePublish(id: number) {
    try {
      await apiFetch(`/admin/news/${id}`, {
        method: "PUT",
        body: JSON.stringify({ status: "published" }),
      });
      loadArticles();
    } catch (err) {
      alert(err instanceof ApiError ? err.message : "操作失败");
    }
  }

  async function handleDelete(id: number) {
    if (!confirm("确定删除这篇资讯吗？")) return;
    try {
      await apiFetch(`/admin/news/${id}`, { method: "DELETE" });
      loadArticles();
    } catch (err) {
      alert(err instanceof ApiError ? err.message : "删除失败");
    }
  }

  function formatDate(dateStr: string) {
    return new Date(dateStr).toLocaleDateString("zh-CN");
  }

  return (
    <div className="mx-auto max-w-5xl px-4 py-8">
      <h1 className="mb-6 text-2xl font-bold">新闻管理</h1>

      <div className="mb-4 flex gap-2">
        {(["all", "pending", "published"] as const).map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`rounded-md px-3 py-1 text-sm ${
              filter === f
                ? "bg-foreground text-background"
                : "bg-foreground/5 hover:bg-foreground/10"
            }`}
          >
            {f === "all" ? "全部" : f === "pending" ? "待审核" : "已发布"}
          </button>
        ))}
      </div>

      {loading ? (
        <p className="text-foreground/50">加载中...</p>
      ) : articles.length === 0 ? (
        <p className="text-foreground/50">暂无资讯</p>
      ) : (
        <div className="space-y-3">
          {articles.map((a) => (
            <div
              key={a.id}
              className="flex items-start justify-between rounded-md border border-foreground/10 p-4"
            >
              <div className="min-w-0 flex-1">
                <Link
                  href={`/news/${a.slug}`}
                  className="font-medium hover:underline"
                >
                  {a.title}
                </Link>
                <div className="mt-1 flex items-center gap-2 text-xs text-foreground/50">
                  <time>{formatDate(a.created_at)}</time>
                  {a.source_name && <span>{a.source_name}</span>}
                  {a.category && <span>{a.category}</span>}
                  <span
                    className={`rounded-full px-2 py-0.5 ${
                      a.status === "published"
                        ? "bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300"
                        : "bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300"
                    }`}
                  >
                    {a.status === "published" ? "已发布" : "待审核"}
                  </span>
                </div>
              </div>
              <div className="flex shrink-0 gap-2 ml-4">
                {a.status === "pending" && (
                  <button
                    onClick={() => handlePublish(a.id)}
                    className="text-xs text-green-600 hover:text-green-800"
                  >
                    发布
                  </button>
                )}
                <button
                  onClick={() => handleDelete(a.id)}
                  className="text-xs text-red-500 hover:text-red-700"
                >
                  删除
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
