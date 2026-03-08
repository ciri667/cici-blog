"use client";

import PostForm from "@/components/PostForm";

export default function NewPostPage() {
  return (
    <div className="mx-auto max-w-4xl px-4 py-8">
      <h1 className="mb-6 text-2xl font-bold">新建文章</h1>
      <PostForm />
    </div>
  );
}
