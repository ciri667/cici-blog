"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { apiFetch, ApiError } from "@/lib/api";
import type { NewsListItem } from "@/lib/types";

type NewsStatusFilter = "all" | "pending" | "published";
type EditableStatus = "pending" | "published";

interface EditFormState {
  title: string;
  summary: string;
  category: string;
  tags: string;
  status: EditableStatus;
}

export default function AdminNewsPage() {
  const [articles, setArticles] = useState<NewsListItem[]>([]);
  const [filter, setFilter] = useState<NewsStatusFilter>("all");
  const [loading, setLoading] = useState(true);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editForm, setEditForm] = useState<EditFormState>({
    title: "",
    summary: "",
    category: "",
    tags: "",
    status: "pending",
  });

  const loadArticles = useCallback(async () => {
    setLoading(true);
    try {
      const params = filter === "all" ? "" : `?status=${filter}`;
      const data = await apiFetch<{ items: NewsListItem[] }>(`/admin/news${params}`);
      setArticles(data.items);
    } catch {
      setArticles([]);
    } finally {
      setLoading(false);
    }
  }, [filter]);

  useEffect(() => {
    void loadArticles();
  }, [loadArticles]);

  async function handlePublish(id: number) {
    try {
      await apiFetch(`/admin/news/${id}`, {
        method: "PUT",
        body: JSON.stringify({ status: "published" }),
      });
      void loadArticles();
    } catch (err) {
      alert(err instanceof ApiError ? err.message : "操作失败");
    }
  }

  async function handleSaveEdit(id: number) {
    try {
      await apiFetch(`/admin/news/${id}`, {
        method: "PUT",
        body: JSON.stringify({
          title: editForm.title.trim() || undefined,
          summary: editForm.summary.trim() || null,
          category: editForm.category.trim() || null,
          tags: editForm.tags
            .split(",")
            .map((value) => value.trim())
            .filter(Boolean),
          status: editForm.status,
        }),
      });
      setEditingId(null);
      void loadArticles();
    } catch (err) {
      alert(err instanceof ApiError ? err.message : "保存失败");
    }
  }

  async function handleDelete(id: number) {
    if (!confirm("确定删除这篇资讯吗？")) {
      return;
    }

    try {
      await apiFetch(`/admin/news/${id}`, { method: "DELETE" });
      void loadArticles();
    } catch (err) {
      alert(err instanceof ApiError ? err.message : "删除失败");
    }
  }

  function startEdit(article: NewsListItem) {
    setEditingId(article.id);
    setEditForm({
      title: article.title,
      summary: article.summary || "",
      category: article.category || "",
      tags: (article.tags || []).join(", "),
      status: article.status === "published" ? "published" : "pending",
    });
  }

  function formatDate(dateStr: string) {
    return new Date(dateStr).toLocaleDateString("zh-CN");
  }

  return (
    <div className="mx-auto max-w-5xl px-4 py-8">
      <h1 className="mb-6 text-2xl font-bold">新闻管理</h1>

      <div className="mb-4 flex gap-2">
        {(["all", "pending", "published"] as const).map((value) => (
          <button
            key={value}
            onClick={() => setFilter(value)}
            className={`rounded-md px-3 py-1 text-sm ${
              filter === value
                ? "bg-foreground text-background"
                : "bg-foreground/5 hover:bg-foreground/10"
            }`}
          >
            {value === "all" ? "全部" : value === "pending" ? "待审核" : "已发布"}
          </button>
        ))}
      </div>

      {loading ? (
        <p className="text-foreground/50">加载中...</p>
      ) : articles.length === 0 ? (
        <p className="text-foreground/50">暂无资讯</p>
      ) : (
        <div className="space-y-3">
          {articles.map((article) => (
            <div
              key={article.id}
              className="flex items-start justify-between rounded-md border border-foreground/10 p-4"
            >
              <div className="min-w-0 flex-1">
                {editingId === article.id ? (
                  <div className="space-y-2">
                    <input
                      value={editForm.title}
                      onChange={(event) =>
                        setEditForm((prev) => ({ ...prev, title: event.target.value }))
                      }
                      className="w-full rounded border border-foreground/20 px-2 py-1 text-sm"
                      placeholder="标题"
                    />
                    <textarea
                      value={editForm.summary}
                      onChange={(event) =>
                        setEditForm((prev) => ({ ...prev, summary: event.target.value }))
                      }
                      className="w-full rounded border border-foreground/20 px-2 py-1 text-sm"
                      rows={3}
                      placeholder="摘要"
                    />
                    <div className="grid gap-2 sm:grid-cols-2">
                      <input
                        value={editForm.category}
                        onChange={(event) =>
                          setEditForm((prev) => ({ ...prev, category: event.target.value }))
                        }
                        className="rounded border border-foreground/20 px-2 py-1 text-sm"
                        placeholder="分类"
                      />
                      <input
                        value={editForm.tags}
                        onChange={(event) =>
                          setEditForm((prev) => ({ ...prev, tags: event.target.value }))
                        }
                        className="rounded border border-foreground/20 px-2 py-1 text-sm"
                        placeholder="标签，逗号分隔"
                      />
                    </div>
                    <select
                      value={editForm.status}
                      onChange={(event) =>
                        setEditForm((prev) => ({
                          ...prev,
                          status: event.target.value as EditableStatus,
                        }))
                      }
                      className="rounded border border-foreground/20 px-2 py-1 text-sm"
                    >
                      <option value="pending">待审核</option>
                      <option value="published">已发布</option>
                    </select>
                  </div>
                ) : (
                  <Link href={`/news/${article.slug}`} className="font-medium hover:underline">
                    {article.title}
                  </Link>
                )}

                <div className="mt-1 flex items-center gap-2 text-xs text-foreground/50">
                  <time>{formatDate(article.published_at || article.created_at)}</time>
                  {article.source_name && <span>{article.source_name}</span>}
                  {article.category && <span>{article.category}</span>}
                  <span
                    className={`rounded-full px-2 py-0.5 ${
                      article.status === "published"
                        ? "bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300"
                        : "bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300"
                    }`}
                  >
                    {article.status === "published" ? "已发布" : "待审核"}
                  </span>
                </div>
              </div>

              <div className="ml-4 flex shrink-0 gap-2">
                {editingId === article.id ? (
                  <>
                    <button
                      onClick={() => void handleSaveEdit(article.id)}
                      className="text-xs text-blue-600 hover:text-blue-800"
                    >
                      保存
                    </button>
                    <button
                      onClick={() => setEditingId(null)}
                      className="text-xs text-foreground/60 hover:text-foreground/80"
                    >
                      取消
                    </button>
                  </>
                ) : (
                  <>
                    <button
                      onClick={() => startEdit(article)}
                      className="text-xs text-blue-600 hover:text-blue-800"
                    >
                      编辑
                    </button>
                    {article.status === "pending" && (
                      <button
                        onClick={() => void handlePublish(article.id)}
                        className="text-xs text-green-600 hover:text-green-800"
                      >
                        发布
                      </button>
                    )}
                  </>
                )}
                <button
                  onClick={() => void handleDelete(article.id)}
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
