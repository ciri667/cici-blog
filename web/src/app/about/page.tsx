import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "关于",
  description: "关于 Cici Blog",
};

export default function AboutPage() {
  return (
    <main className="mx-auto max-w-3xl px-4 py-12">
      <h1 className="mb-6 text-3xl font-bold">关于</h1>
      <div className="prose prose-neutral dark:prose-invert max-w-none">
        <p>
          欢迎来到 Cici Blog，这是一个融合了个人博客与 AI
          驱动科技资讯的平台。
        </p>
        <h2>博客</h2>
        <p>
          在博客板块，我分享技术心得、项目经验和个人思考。涵盖 Web
          开发、人工智能、系统架构等多个领域。
        </p>
        <h2>AI 科技资讯</h2>
        <p>
          资讯板块由 AI Agent
          自动运行，定时从全球科技媒体和信息源采集最新动态，并利用大语言模型生成深度分析评论。每篇资讯都标注了
          AI 生成标识和原始来源链接。
        </p>
        <h2>技术栈</h2>
        <ul>
          <li>前端: Next.js + React + TypeScript + Tailwind CSS</li>
          <li>后端: FastAPI + Python</li>
          <li>数据库: PostgreSQL</li>
          <li>AI: Claude API + GPT-4o-mini + Tavily Search</li>
          <li>存储: Cloudflare R2 + CDN</li>
        </ul>
      </div>
    </main>
  );
}
