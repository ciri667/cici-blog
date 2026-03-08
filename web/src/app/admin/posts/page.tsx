"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiFetch, ApiError } from "@/lib/api";
import type { PostListResponse, PostListItem } from "@/lib/types";

export default function AdminPostsPage() {
  const [posts, setPosts] = useState<PostListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);

  async function loadPosts(p: number) {
    setLoading(true);
    try {
      const data = await apiFetch<PostListResponse>(
        `/posts?page=${p}&page_size=20&status=draft`,
      );
      // 同时加载已发布的文章并合并
      const published = await apiFetch<PostListResponse>(
        `/posts?page=${p}&page_size=20&status=published`,
      );
      setPosts([...data.items, ...published.items]);
      setTotal(data.total + published.total);
    } catch {
      setPosts([]);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadPosts(page);
  }, [page]);

  async function handleDelete(id: number) {
    if (!confirm("确定删除这篇文章吗？")) return;
    try {
      await apiFetch(`/posts/${id}`, { method: "DELETE" });
      loadPosts(page);
    } catch (err) {
      alert(err instanceof ApiError ? err.message : "删除失败");
    }
  }

  function formatDate(dateStr: string | null) {
    if (!dateStr) return "-";
    return new Date(dateStr).toLocaleDateString("zh-CN");
  }

  return (
    <div className="mx-auto max-w-5xl px-4 py-8">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold">文章管理</h1>
        <Link
          href="/admin/posts/new"
          className="rounded-md bg-foreground px-4 py-2 text-sm font-medium text-background hover:opacity-90"
        >
          新建文章
        </Link>
      </div>

      {loading ? (
        <p className="text-foreground/50">加载中...</p>
      ) : posts.length === 0 ? (
        <p className="text-foreground/50">暂无文章</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-foreground/10">
              <tr>
                <th className="pb-3 font-medium">标题</th>
                <th className="pb-3 font-medium">状态</th>
                <th className="pb-3 font-medium">分类</th>
                <th className="pb-3 font-medium">创建时间</th>
                <th className="pb-3 font-medium">操作</th>
              </tr>
            </thead>
            <tbody>
              {posts.map((post) => (
                <tr key={post.id} className="border-b border-foreground/5">
                  <td className="py-3 pr-4">
                    <Link
                      href={`/blog/${post.slug}`}
                      className="hover:underline"
                    >
                      {post.title}
                    </Link>
                  </td>
                  <td className="py-3 pr-4">
                    <span
                      className={`rounded-full px-2 py-0.5 text-xs ${
                        post.status === "published"
                          ? "bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300"
                          : "bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300"
                      }`}
                    >
                      {post.status === "published" ? "已发布" : "草稿"}
                    </span>
                  </td>
                  <td className="py-3 pr-4 text-foreground/60">
                    {post.category || "-"}
                  </td>
                  <td className="py-3 pr-4 text-foreground/60">
                    {formatDate(post.created_at)}
                  </td>
                  <td className="py-3">
                    <div className="flex gap-2">
                      <Link
                        href={`/admin/posts/${post.id}/edit`}
                        className="text-foreground/60 hover:text-foreground"
                      >
                        编辑
                      </Link>
                      <button
                        onClick={() => handleDelete(post.id)}
                        className="text-red-500 hover:text-red-700"
                      >
                        删除
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
