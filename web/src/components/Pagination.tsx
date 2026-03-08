"use client";

import Link from "next/link";

interface PaginationProps {
  page: number;
  totalPages: number;
  basePath: string;
  queryParams?: Record<string, string>;
}

export default function Pagination({
  page,
  totalPages,
  basePath,
  queryParams = {},
}: PaginationProps) {
  if (totalPages <= 1) return null;

  function buildHref(p: number) {
    const params = new URLSearchParams(queryParams);
    if (p > 1) params.set("page", String(p));
    const qs = params.toString();
    return qs ? `${basePath}?${qs}` : basePath;
  }

  const pages: (number | "...")[] = [];
  for (let i = 1; i <= totalPages; i++) {
    if (i === 1 || i === totalPages || (i >= page - 1 && i <= page + 1)) {
      pages.push(i);
    } else if (pages[pages.length - 1] !== "...") {
      pages.push("...");
    }
  }

  return (
    <nav className="flex items-center justify-center gap-1 py-8">
      {page > 1 && (
        <Link
          href={buildHref(page - 1)}
          className="rounded-md px-3 py-2 text-sm hover:bg-foreground/5"
        >
          上一页
        </Link>
      )}

      {pages.map((p, i) =>
        p === "..." ? (
          <span key={`ellipsis-${i}`} className="px-2 text-foreground/40">
            ...
          </span>
        ) : (
          <Link
            key={p}
            href={buildHref(p)}
            className={`rounded-md px-3 py-2 text-sm ${
              p === page
                ? "bg-foreground text-background font-medium"
                : "hover:bg-foreground/5"
            }`}
          >
            {p}
          </Link>
        ),
      )}

      {page < totalPages && (
        <Link
          href={buildHref(page + 1)}
          className="rounded-md px-3 py-2 text-sm hover:bg-foreground/5"
        >
          下一页
        </Link>
      )}
    </nav>
  );
}
