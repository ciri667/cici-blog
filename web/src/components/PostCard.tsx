import Link from "next/link";
import type { PostListItem } from "@/lib/types";

function formatDate(dateStr: string | null) {
  if (!dateStr) return "";
  return new Date(dateStr).toLocaleDateString("zh-CN", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });
}

export default function PostCard({ post }: { post: PostListItem }) {
  return (
    <article className="border-b border-foreground/10 py-6 first:pt-0 last:border-b-0">
      <div className="flex gap-6">
        {post.cover_image_url && (
          <div className="hidden sm:block shrink-0">
            <img
              src={post.cover_image_url}
              alt={post.title}
              className="h-32 w-48 rounded-md object-cover"
            />
          </div>
        )}
        <div className="min-w-0 flex-1">
          <Link href={`/blog/${post.slug}`}>
            <h2 className="text-lg font-semibold leading-tight hover:underline">
              {post.title}
            </h2>
          </Link>

          {post.excerpt && (
            <p className="mt-2 text-sm leading-relaxed text-foreground/60 line-clamp-2">
              {post.excerpt}
            </p>
          )}

          <div className="mt-3 flex flex-wrap items-center gap-2 text-xs text-foreground/50">
            <time>{formatDate(post.published_at || post.created_at)}</time>

            {post.category && (
              <Link
                href={`/blog/category/${post.category}`}
                className="hover:text-foreground"
              >
                {post.category}
              </Link>
            )}

            {post.tags?.map((tag) => (
              <Link
                key={tag}
                href={`/blog/tag/${tag}`}
                className="rounded-full bg-foreground/5 px-2 py-0.5 hover:bg-foreground/10"
              >
                {tag}
              </Link>
            ))}
          </div>
        </div>
      </div>
    </article>
  );
}
