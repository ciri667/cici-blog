"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { apiFetch, ApiError } from "@/lib/api";
import MarkdownEditor from "./MarkdownEditor";
import type { Post } from "@/lib/types";

interface PostFormProps {
  post?: Post;
}

export default function PostForm({ post }: PostFormProps) {
  const router = useRouter();
  const [title, setTitle] = useState(post?.title || "");
  const [content, setContent] = useState(post?.content || "");
  const [excerpt, setExcerpt] = useState(post?.excerpt || "");
  const [category, setCategory] = useState(post?.category || "");
  const [tags, setTags] = useState(post?.tags?.join(", ") || "");
  const [coverImageUrl, setCoverImageUrl] = useState(post?.cover_image_url || "");
  const [status, setStatus] = useState(post?.status || "draft");
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setSaving(true);

    const tagList = tags
      .split(",")
      .map((t) => t.trim())
      .filter(Boolean);

    const body = {
      title,
      content,
      excerpt: excerpt || null,
      cover_image_url: coverImageUrl || null,
      tags: tagList.length > 0 ? tagList : null,
      category: category || null,
      status,
    };

    try {
      if (post) {
        await apiFetch(`/posts/${post.id}`, {
          method: "PUT",
          body: JSON.stringify(body),
        });
      } else {
        await apiFetch("/posts", {
          method: "POST",
          body: JSON.stringify(body),
        });
      }
      router.push("/admin/posts");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "保存失败");
    } finally {
      setSaving(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {error && (
        <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-800 dark:bg-red-950 dark:text-red-300">
          {error}
        </div>
      )}

      <div>
        <label htmlFor="title" className="block text-sm font-medium">
          标题
        </label>
        <input
          id="title"
          type="text"
          required
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          className="mt-1 block w-full rounded-md border border-foreground/20 bg-background px-3 py-2 text-sm shadow-sm focus:border-foreground/50 focus:outline-none focus:ring-1 focus:ring-foreground/50"
        />
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div>
          <label htmlFor="category" className="block text-sm font-medium">
            分类
          </label>
          <input
            id="category"
            type="text"
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            className="mt-1 block w-full rounded-md border border-foreground/20 bg-background px-3 py-2 text-sm shadow-sm focus:border-foreground/50 focus:outline-none focus:ring-1 focus:ring-foreground/50"
            placeholder="如：技术、随笔"
          />
        </div>
        <div>
          <label htmlFor="tags" className="block text-sm font-medium">
            标签（逗号分隔）
          </label>
          <input
            id="tags"
            type="text"
            value={tags}
            onChange={(e) => setTags(e.target.value)}
            className="mt-1 block w-full rounded-md border border-foreground/20 bg-background px-3 py-2 text-sm shadow-sm focus:border-foreground/50 focus:outline-none focus:ring-1 focus:ring-foreground/50"
            placeholder="React, Next.js, TypeScript"
          />
        </div>
      </div>

      <div>
        <label htmlFor="excerpt" className="block text-sm font-medium">
          摘要
        </label>
        <textarea
          id="excerpt"
          value={excerpt}
          onChange={(e) => setExcerpt(e.target.value)}
          rows={2}
          className="mt-1 block w-full rounded-md border border-foreground/20 bg-background px-3 py-2 text-sm shadow-sm focus:border-foreground/50 focus:outline-none focus:ring-1 focus:ring-foreground/50"
          placeholder="文章摘要，显示在列表页"
        />
      </div>

      <div>
        <label htmlFor="cover" className="block text-sm font-medium">
          封面图 URL
        </label>
        <input
          id="cover"
          type="url"
          value={coverImageUrl}
          onChange={(e) => setCoverImageUrl(e.target.value)}
          className="mt-1 block w-full rounded-md border border-foreground/20 bg-background px-3 py-2 text-sm shadow-sm focus:border-foreground/50 focus:outline-none focus:ring-1 focus:ring-foreground/50"
          placeholder="https://cdn.example.com/image.jpg"
        />
      </div>

      <div>
        <label className="block text-sm font-medium mb-1">正文（Markdown）</label>
        <MarkdownEditor value={content} onChange={setContent} />
      </div>

      <div className="flex items-center gap-4">
        <select
          value={status}
          onChange={(e) => setStatus(e.target.value)}
          className="rounded-md border border-foreground/20 bg-background px-3 py-2 text-sm"
        >
          <option value="draft">草稿</option>
          <option value="published">发布</option>
        </select>

        <button
          type="submit"
          disabled={saving}
          className="rounded-md bg-foreground px-6 py-2 text-sm font-medium text-background hover:opacity-90 disabled:opacity-50"
        >
          {saving ? "保存中..." : post ? "更新文章" : "创建文章"}
        </button>

        <button
          type="button"
          onClick={() => router.push("/admin/posts")}
          className="text-sm text-foreground/50 hover:text-foreground"
        >
          取消
        </button>
      </div>
    </form>
  );
}
