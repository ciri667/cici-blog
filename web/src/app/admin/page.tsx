import Link from "next/link";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "后台管理",
  description: "Cici Blog 后台管理入口",
};

const ADMIN_MODULES = [
  {
    href: "/admin/posts",
    title: "文章管理",
    description: "创建、编辑、发布与删除博客文章。",
  },
  {
    href: "/admin/news",
    title: "资讯管理",
    description: "审核和管理 AI Agent 生成的资讯内容。",
  },
  {
    href: "/admin/comments",
    title: "评论管理",
    description: "审核、通过、拒绝或删除评论。",
  },
  {
    href: "/admin/agent",
    title: "Agent 控制台",
    description: "查看运行状态、管理 RSS 源并手动触发流水线。",
  },
];

export default function AdminHomePage() {
  return (
    <main className="mx-auto max-w-5xl px-4 py-8">
      <header className="mb-8">
        <h1 className="text-2xl font-bold">后台管理</h1>
        <p className="mt-2 text-sm text-foreground/60">
          选择一个模块进入管理页面。
        </p>
      </header>

      <div className="grid gap-4 sm:grid-cols-2">
        {ADMIN_MODULES.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className="rounded-md border border-foreground/10 p-4 transition-colors hover:border-foreground/30 hover:bg-foreground/[0.02]"
          >
            <h2 className="text-base font-semibold">{item.title}</h2>
            <p className="mt-2 text-sm text-foreground/60">{item.description}</p>
          </Link>
        ))}
      </div>
    </main>
  );
}
