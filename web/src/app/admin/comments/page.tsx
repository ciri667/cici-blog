"use client";

import { useEffect, useState } from "react";
import { apiFetch, ApiError } from "@/lib/api";

interface Comment {
  id: number;
  post_id: number;
  author_name: string | null;
  author_email: string | null;
  content: string;
  is_approved: boolean;
  created_at: string;
}

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleDateString("zh-CN", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function AdminCommentsPage() {
  const [comments, setComments] = useState<Comment[]>([]);
  const [filter, setFilter] = useState<"all" | "pending" | "approved">("all");
  const [loading, setLoading] = useState(true);

  async function loadComments() {
    setLoading(true);
    try {
      const params =
        filter === "all"
          ? ""
          : `?is_approved=${filter === "approved"}`;
      const data = await apiFetch<{ items: Comment[] }>(
        `/admin/comments${params}`,
      );
      setComments(data.items);
    } catch {
      setComments([]);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadComments();
  }, [filter]);

  async function handleApprove(id: number, approve: boolean) {
    try {
      await apiFetch(`/admin/comments/${id}`, {
        method: "PUT",
        body: JSON.stringify({ is_approved: approve }),
      });
      loadComments();
    } catch (err) {
      alert(err instanceof ApiError ? err.message : "操作失败");
    }
  }

  async function handleDelete(id: number) {
    if (!confirm("确定删除这条评论吗？")) return;
    try {
      await apiFetch(`/admin/comments/${id}`, { method: "DELETE" });
      loadComments();
    } catch (err) {
      alert(err instanceof ApiError ? err.message : "删除失败");
    }
  }

  return (
    <div className="mx-auto max-w-5xl px-4 py-8">
      <h1 className="mb-6 text-2xl font-bold">评论管理</h1>

      <div className="mb-4 flex gap-2">
        {(["all", "pending", "approved"] as const).map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`rounded-md px-3 py-1 text-sm ${
              filter === f
                ? "bg-foreground text-background"
                : "bg-foreground/5 hover:bg-foreground/10"
            }`}
          >
            {f === "all" ? "全部" : f === "pending" ? "待审核" : "已通过"}
          </button>
        ))}
      </div>

      {loading ? (
        <p className="text-foreground/50">加载中...</p>
      ) : comments.length === 0 ? (
        <p className="text-foreground/50">暂无评论</p>
      ) : (
        <div className="space-y-4">
          {comments.map((c) => (
            <div
              key={c.id}
              className="rounded-md border border-foreground/10 p-4"
            >
              <div className="flex items-start justify-between">
                <div>
                  <div className="flex items-center gap-2 text-sm">
                    <span className="font-medium">
                      {c.author_name || "匿名"}
                    </span>
                    {c.author_email && (
                      <span className="text-foreground/40">
                        {c.author_email}
                      </span>
                    )}
                    <time className="text-foreground/40">
                      {formatDate(c.created_at)}
                    </time>
                    <span
                      className={`rounded-full px-2 py-0.5 text-xs ${
                        c.is_approved
                          ? "bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300"
                          : "bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300"
                      }`}
                    >
                      {c.is_approved ? "已通过" : "待审核"}
                    </span>
                  </div>
                  <p className="mt-2 text-sm">{c.content}</p>
                </div>
                <div className="flex shrink-0 gap-2 ml-4">
                  {!c.is_approved && (
                    <button
                      onClick={() => handleApprove(c.id, true)}
                      className="text-xs text-green-600 hover:text-green-800"
                    >
                      通过
                    </button>
                  )}
                  {c.is_approved && (
                    <button
                      onClick={() => handleApprove(c.id, false)}
                      className="text-xs text-yellow-600 hover:text-yellow-800"
                    >
                      撤回
                    </button>
                  )}
                  <button
                    onClick={() => handleDelete(c.id)}
                    className="text-xs text-red-500 hover:text-red-700"
                  >
                    删除
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
