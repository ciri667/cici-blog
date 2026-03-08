"use client";

import { useEffect, useState, FormEvent } from "react";
import { apiFetch, ApiError } from "@/lib/api";

interface Comment {
  id: number;
  author_name: string | null;
  content: string;
  created_at: string;
}

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleDateString("zh-CN", {
    year: "numeric",
    month: "long",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function CommentSection({ postId }: { postId: number }) {
  const [comments, setComments] = useState<Comment[]>([]);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [content, setContent] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    apiFetch<Comment[]>(`/posts/${postId}/comments`)
      .then(setComments)
      .catch(() => {});
  }, [postId]);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setSuccess("");
    setSubmitting(true);

    try {
      await apiFetch(`/posts/${postId}/comments`, {
        method: "POST",
        body: JSON.stringify({
          author_name: name || null,
          author_email: email || null,
          content,
        }),
      });
      setSuccess("评论已提交，等待审核后展示");
      setContent("");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "提交失败");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section className="mt-12 border-t border-foreground/10 pt-8">
      <h2 className="mb-6 text-xl font-bold">评论</h2>

      {comments.length > 0 ? (
        <div className="mb-8 space-y-6">
          {comments.map((c) => (
            <div key={c.id} className="border-b border-foreground/5 pb-4 last:border-b-0">
              <div className="flex items-center gap-2 text-sm text-foreground/50">
                <span className="font-medium text-foreground/80">
                  {c.author_name || "匿名"}
                </span>
                <time>{formatDate(c.created_at)}</time>
              </div>
              <p className="mt-2 text-sm leading-relaxed">{c.content}</p>
            </div>
          ))}
        </div>
      ) : (
        <p className="mb-8 text-sm text-foreground/50">暂无评论</p>
      )}

      <h3 className="mb-4 text-lg font-semibold">发表评论</h3>

      {error && (
        <div className="mb-4 rounded-md border border-red-200 bg-red-50 px-4 py-2 text-sm text-red-700 dark:border-red-800 dark:bg-red-950 dark:text-red-300">
          {error}
        </div>
      )}
      {success && (
        <div className="mb-4 rounded-md border border-green-200 bg-green-50 px-4 py-2 text-sm text-green-700 dark:border-green-800 dark:bg-green-950 dark:text-green-300">
          {success}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <input
            type="text"
            placeholder="昵称"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="rounded-md border border-foreground/20 bg-background px-3 py-2 text-sm focus:border-foreground/50 focus:outline-none focus:ring-1 focus:ring-foreground/50"
          />
          <input
            type="email"
            placeholder="邮箱（不公开）"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="rounded-md border border-foreground/20 bg-background px-3 py-2 text-sm focus:border-foreground/50 focus:outline-none focus:ring-1 focus:ring-foreground/50"
          />
        </div>
        <textarea
          required
          placeholder="写下你的评论..."
          value={content}
          onChange={(e) => setContent(e.target.value)}
          rows={4}
          className="block w-full rounded-md border border-foreground/20 bg-background px-3 py-2 text-sm focus:border-foreground/50 focus:outline-none focus:ring-1 focus:ring-foreground/50"
        />
        <button
          type="submit"
          disabled={submitting}
          className="rounded-md bg-foreground px-4 py-2 text-sm font-medium text-background hover:opacity-90 disabled:opacity-50"
        >
          {submitting ? "提交中..." : "提交评论"}
        </button>
      </form>
    </section>
  );
}
