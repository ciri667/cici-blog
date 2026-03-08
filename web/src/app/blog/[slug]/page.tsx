import { notFound } from "next/navigation";
import Link from "next/link";
import type { Metadata } from "next";
import MarkdownRenderer from "@/components/MarkdownRenderer";
import CommentSection from "@/components/CommentSection";
import type { Post } from "@/lib/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

async function getPost(slug: string): Promise<Post | null> {
  const res = await fetch(`${API_BASE}/posts/${slug}`, {
    next: { revalidate: 60 },
  });
  if (!res.ok) return null;
  return res.json();
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const { slug } = await params;
  const post = await getPost(slug);
  if (!post) return { title: "文章不存在" };

  return {
    title: post.title,
    description: post.excerpt || post.title,
    openGraph: {
      title: post.title,
      description: post.excerpt || post.title,
      type: "article",
      publishedTime: post.published_at || undefined,
      images: post.cover_image_url ? [post.cover_image_url] : undefined,
    },
  };
}

function formatDate(dateStr: string | null) {
  if (!dateStr) return "";
  return new Date(dateStr).toLocaleDateString("zh-CN", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });
}

export default async function BlogPostPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const post = await getPost(slug);
  if (!post) notFound();

  return (
    <main className="mx-auto max-w-3xl px-4 py-12">
      <article>
        <header className="mb-8">
          <h1 className="text-3xl font-bold leading-tight">{post.title}</h1>
          <div className="mt-3 flex flex-wrap items-center gap-2 text-sm text-foreground/50">
            <time>{formatDate(post.published_at || post.created_at)}</time>
            {post.category && (
              <Link
                href={`/blog/category/${post.category}`}
                className="hover:text-foreground"
              >
                {post.category}
              </Link>
            )}
          </div>
          {post.tags && post.tags.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-2">
              {post.tags.map((tag) => (
                <Link
                  key={tag}
                  href={`/blog/tag/${tag}`}
                  className="rounded-full bg-foreground/5 px-3 py-1 text-xs hover:bg-foreground/10"
                >
                  {tag}
                </Link>
              ))}
            </div>
          )}
        </header>

        {post.cover_image_url && (
          <img
            src={post.cover_image_url}
            alt={post.title}
            className="mb-8 w-full rounded-lg object-cover"
          />
        )}

        <MarkdownRenderer content={post.content} />
      </article>

      <CommentSection postId={post.id} />

      <div className="mt-12 border-t border-foreground/10 pt-6">
        <Link href="/" className="text-sm text-foreground/50 hover:text-foreground">
          ← 返回首页
        </Link>
      </div>
    </main>
  );
}
