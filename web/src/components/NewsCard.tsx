import Link from "next/link";
import type { NewsListItem } from "@/lib/types";

function formatDate(dateStr: string | null) {
  if (!dateStr) return "";
  return new Date(dateStr).toLocaleDateString("zh-CN", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });
}

export default function NewsCard({ article }: { article: NewsListItem }) {
  return (
    <article className="border-b border-foreground/10 py-5 first:pt-0 last:border-b-0">
      <Link href={`/news/${article.slug}`}>
        <h2 className="text-lg font-semibold leading-tight hover:underline">
          {article.title}
        </h2>
      </Link>

      {article.summary && (
        <p className="mt-2 text-sm leading-relaxed text-foreground/60 line-clamp-2">
          {article.summary}
        </p>
      )}

      <div className="mt-3 flex flex-wrap items-center gap-2 text-xs text-foreground/50">
        <time>{formatDate(article.published_at || article.created_at)}</time>

        {article.source_name && (
          <span className="text-foreground/40">{article.source_name}</span>
        )}

        {article.category && (
          <Link
            href={`/news/category/${article.category}`}
            className="hover:text-foreground"
          >
            {article.category}
          </Link>
        )}

        {article.tags?.map((tag) => (
          <span
            key={tag}
            className="rounded-full bg-foreground/5 px-2 py-0.5"
          >
            {tag}
          </span>
        ))}

        <span className="rounded bg-blue-50 px-1.5 py-0.5 text-blue-600 dark:bg-blue-950 dark:text-blue-400">
          AI 生成
        </span>
      </div>
    </article>
  );
}
