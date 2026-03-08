import NewsCard from "@/components/NewsCard";
import Pagination from "@/components/Pagination";
import type { NewsListResponse } from "@/lib/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

async function getNews(page: number): Promise<NewsListResponse> {
  const res = await fetch(`${API_BASE}/news?page=${page}&page_size=10`, {
    next: { revalidate: 60 },
  });
  if (!res.ok) return { items: [], total: 0, page: 1, page_size: 10 };
  return res.json();
}

export default async function NewsPage({
  searchParams,
}: {
  searchParams: Promise<{ page?: string }>;
}) {
  const params = await searchParams;
  const page = Math.max(1, Number(params.page) || 1);
  const data = await getNews(page);
  const totalPages = Math.ceil(data.total / data.page_size);

  return (
    <main className="mx-auto max-w-3xl px-4 py-12">
      <h1 className="mb-8 text-3xl font-bold">科技资讯</h1>
      <p className="mb-6 text-sm text-foreground/50">
        AI 驱动的科技新闻资讯，自动采集并生成评论分析
      </p>

      {data.items.length === 0 ? (
        <p className="text-foreground/50">暂无资讯</p>
      ) : (
        <>
          <div>
            {data.items.map((article) => (
              <NewsCard key={article.id} article={article} />
            ))}
          </div>
          <Pagination page={page} totalPages={totalPages} basePath="/news" />
        </>
      )}
    </main>
  );
}
