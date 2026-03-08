"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { apiFetch } from "@/lib/api";
import PostForm from "@/components/PostForm";
import type { Post } from "@/lib/types";

export default function EditPostPage() {
  const params = useParams<{ id: string }>();
  const [post, setPost] = useState<Post | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    // We need to find the post by ID. The API uses slug for GET,
    // so we fetch all posts and find by ID, or use a dedicated approach.
    // For simplicity, we'll add a query to find by listing.
    async function loadPost() {
      try {
        // Fetch drafts and published to find by id
        for (const status of ["draft", "published"]) {
          const data = await apiFetch<{ items: Post[] }>(
            `/posts?status=${status}&page_size=100`,
          );
          const found = data.items.find((p) => p.id === Number(params.id));
          if (found) {
            // Fetch full post with content by slug
            const full = await apiFetch<Post>(`/posts/${found.slug}`);
            setPost(full);
            return;
          }
        }
        setError("文章不存在");
      } catch {
        setError("加载文章失败");
      } finally {
        setLoading(false);
      }
    }
    loadPost();
  }, [params.id]);

  if (loading) {
    return (
      <div className="mx-auto max-w-4xl px-4 py-8">
        <p className="text-foreground/50">加载中...</p>
      </div>
    );
  }

  if (error || !post) {
    return (
      <div className="mx-auto max-w-4xl px-4 py-8">
        <p className="text-red-500">{error || "文章不存在"}</p>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl px-4 py-8">
      <h1 className="mb-6 text-2xl font-bold">编辑文章</h1>
      <PostForm post={post} />
    </div>
  );
}
