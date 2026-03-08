import PostCard from "@/components/PostCard";
import Pagination from "@/components/Pagination";
import type { PostListResponse } from "@/lib/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

async function getPosts(page: number): Promise<PostListResponse> {
  const res = await fetch(`${API_BASE}/posts?page=${page}&page_size=10`, {
    next: { revalidate: 60 },
  });
  if (!res.ok) {
    return { items: [], total: 0, page: 1, page_size: 10 };
  }
  return res.json();
}

export default async function HomePage({
  searchParams,
}: {
  searchParams: Promise<{ page?: string }>;
}) {
  const params = await searchParams;
  const page = Math.max(1, Number(params.page) || 1);
  const data = await getPosts(page);
  const totalPages = Math.ceil(data.total / data.page_size);

  return (
    <main className="mx-auto max-w-3xl px-4 py-12">
      <h1 className="mb-8 text-3xl font-bold">博客</h1>

      {data.items.length === 0 ? (
        <p className="text-foreground/50">暂无文章</p>
      ) : (
        <>
          <div>
            {data.items.map((post) => (
              <PostCard key={post.id} post={post} />
            ))}
          </div>
          <Pagination page={page} totalPages={totalPages} basePath="/" />
        </>
      )}
    </main>
  );
}
