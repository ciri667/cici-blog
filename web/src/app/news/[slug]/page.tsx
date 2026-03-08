import { notFound } from "next/navigation";
import Link from "next/link";
import type { Metadata } from "next";
import MarkdownRenderer from "@/components/MarkdownRenderer";
import type { NewsArticle } from "@/lib/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

async function getArticle(slug: string): Promise<NewsArticle | null> {
  const res = await fetch(`${API_BASE}/news/${slug}`, {
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
  const article = await getArticle(slug);
  if (!article) return { title: "文章不存在" };

  return {
    title: article.title,
    description: article.summary || article.title,
    openGraph: {
      title: article.title,
      description: article.summary || article.title,
      type: "article",
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

export default async function NewsArticlePage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const article = await getArticle(slug);
  if (!article) notFound();

  return (
    <main className="mx-auto max-w-3xl px-4 py-12">
      <article>
        <header className="mb-8">
          <span className="mb-2 inline-block rounded bg-blue-50 px-2 py-1 text-xs text-blue-600 dark:bg-blue-950 dark:text-blue-400">
            AI 生成内容
          </span>
          <h1 className="text-3xl font-bold leading-tight">{article.title}</h1>
          <div className="mt-3 flex flex-wrap items-center gap-2 text-sm text-foreground/50">
            <time>{formatDate(article.published_at || article.created_at)}</time>
            {article.source_name && <span>{article.source_name}</span>}
            {article.category && (
              <Link
                href={`/news/category/${article.category}`}
                className="hover:text-foreground"
              >
                {article.category}
              </Link>
            )}
          </div>
          {article.tags && article.tags.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-2">
              {article.tags.map((tag) => (
                <span
                  key={tag}
                  className="rounded-full bg-foreground/5 px-3 py-1 text-xs"
                >
                  {tag}
                </span>
              ))}
            </div>
          )}
        </header>

        {article.summary && (
          <div className="mb-6 rounded-md border border-foreground/10 bg-foreground/[0.02] p-4">
            <h3 className="mb-2 text-sm font-semibold text-foreground/70">摘要</h3>
            <p className="text-sm leading-relaxed">{article.summary}</p>
          </div>
        )}

        {article.ai_commentary && (
          <MarkdownRenderer content={article.ai_commentary} />
        )}

        <div className="mt-8 rounded-md border border-foreground/10 p-4">
          <p className="text-sm text-foreground/50">
            原始来源：{" "}
            <a
              href={article.original_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-foreground/70 underline hover:text-foreground"
            >
              {article.original_title}
            </a>
          </p>
        </div>
      </article>

      <div className="mt-12 border-t border-foreground/10 pt-6">
        <Link href="/news" className="text-sm text-foreground/50 hover:text-foreground">
          ← 返回资讯列表
        </Link>
      </div>
    </main>
  );
}
