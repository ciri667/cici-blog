import NewsCard from "@/components/NewsCard";
import Pagination from "@/components/Pagination";
import type { NewsListResponse } from "@/lib/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

async function getNewsByCategory(
  category: string,
  page: number,
): Promise<NewsListResponse> {
  const res = await fetch(
    `${API_BASE}/news?category=${encodeURIComponent(category)}&page=${page}&page_size=10`,
    { next: { revalidate: 60 } },
  );
  if (!res.ok) return { items: [], total: 0, page: 1, page_size: 10 };
  return res.json();
}

export default async function NewsCategoryPage({
  params,
  searchParams,
}: {
  params: Promise<{ name: string }>;
  searchParams: Promise<{ page?: string }>;
}) {
  const { name } = await params;
  const sp = await searchParams;
  const category = decodeURIComponent(name);
  const page = Math.max(1, Number(sp.page) || 1);
  const data = await getNewsByCategory(category, page);
  const totalPages = Math.ceil(data.total / data.page_size);

  return (
    <main className="mx-auto max-w-3xl px-4 py-12">
      <h1 className="mb-8 text-2xl font-bold">
        资讯分类: <span className="text-foreground/70">{category}</span>
      </h1>

      {data.items.length === 0 ? (
        <p className="text-foreground/50">该分类下暂无资讯</p>
      ) : (
        <>
          <div>
            {data.items.map((article) => (
              <NewsCard key={article.id} article={article} />
            ))}
          </div>
          <Pagination
            page={page}
            totalPages={totalPages}
            basePath={`/news/category/${name}`}
          />
        </>
      )}
    </main>
  );
}
