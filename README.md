# cici-blog

一个带有 AI 新闻聚合功能的个人博客平台。

**后端**：FastAPI + PostgreSQL（全异步）
**前端**：Next.js 16 + TypeScript + Tailwind CSS
**AI 能力**：GPT-4o-mini 生成摘要与分类，Claude 生成深度评论

---

## 功能特性

- **博客系统**：Markdown 写作、封面图、标签、分类、草稿/发布状态
- **AI 新闻聚合**：自动从 RSS 订阅源与 Tavily 搜索采集科技资讯，由 AI 生成中文摘要、分类打标、深度评论，每 4 小时自动运行一次
- **用户认证**：支持邮箱密码注册/登录 + Google/GitHub OAuth，JWT 存储于 httponly Cookie（滑动续期）
- **评论系统**：支持游客评论（需审核）和登录用户评论（管理员自动通过），含限流与垃圾评论过滤
- **图片上传**：上传至 Cloudflare R2，通过 CDN 分发（支持 JPG/PNG/WebP/GIF，最大 10MB）
- **管理后台**：文章 CRUD、新闻审核发布、评论管理、RSS 源管理、Agent 手动触发

---

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端框架 | FastAPI + Uvicorn |
| 数据库 | PostgreSQL 16 + SQLAlchemy 2（asyncpg 异步驱动） |
| 数据库迁移 | Alembic |
| 前端框架 | Next.js 16（App Router） |
| 样式 | Tailwind CSS v4 |
| AI — 摘要/分类 | OpenAI GPT-4o-mini |
| AI — 深度评论 | Anthropic Claude (claude-sonnet-4-20250514) |
| 新闻搜索 | Tavily Search API |
| 图片存储 | Cloudflare R2（S3 兼容） |
| 定时任务 | APScheduler |
| 包管理 | uv（后端）、npm（前端） |

---

## 快速开始

### 前置条件

- Python 3.12+，已安装 [uv](https://github.com/astral-sh/uv)
- Node.js 20+
- PostgreSQL 数据库

### 1. 克隆仓库

```bash
git clone <repo-url>
cd cici-blog
```

### 2. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件，填写以下配置（详见[环境变量说明](#环境变量说明)）：

```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/cici_blog
SECRET_KEY=your-secret-key-at-least-32-chars
ADMIN_EMAILS=your-email@example.com
```

### 3. 初始化后端

```bash
# 安装依赖
uv sync

# 初始化数据库并应用迁移
uv run python scripts/ensure_database.py
uv run alembic upgrade head

# 启动开发服务器（:8000）
uv run python main.py
```

### 4. 初始化前端

```bash
cd web

# 配置前端环境变量
echo "NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1" > .env.local

# 安装依赖并启动（:3000）
npm install
npm run dev
```

访问 `http://localhost:3000`，使用 `ADMIN_EMAILS` 中配置的邮箱注册账号即可获得管理员权限。

---

## 环境变量说明

| 变量名 | 必填 | 说明 |
|--------|------|------|
| `DATABASE_URL` | 是（生产） | PostgreSQL 连接串，格式：`postgresql+asyncpg://user:pass@host:port/db` |
| `SECRET_KEY` | 是（生产） | JWT 签名密钥，至少 32 字符。开发环境不填则自动生成（重启后失效） |
| `ENVIRONMENT` | — | `development`（默认）或 `production` |
| `CORS_ORIGINS` | — | 前端地址，多个用逗号分隔，默认 `http://localhost:3000` |
| `ADMIN_EMAILS` | — | 管理员邮箱白名单（逗号分隔），注册时自动赋予 admin 角色 |
| `ADMIN_GITHUB_USERNAMES` | — | 管理员 GitHub 用户名白名单（逗号分隔） |
| `GOOGLE_CLIENT_ID` | — | Google OAuth 客户端 ID |
| `GOOGLE_CLIENT_SECRET` | — | Google OAuth 客户端密钥 |
| `GITHUB_CLIENT_ID` | — | GitHub OAuth App Client ID |
| `GITHUB_CLIENT_SECRET` | — | GitHub OAuth App Client Secret |
| `R2_ACCOUNT_ID` | — | Cloudflare 账户 ID（图片上传功能必填） |
| `R2_ACCESS_KEY_ID` | — | R2 Access Key ID |
| `R2_SECRET_ACCESS_KEY` | — | R2 Secret Access Key |
| `R2_BUCKET_NAME` | — | R2 Bucket 名称 |
| `R2_CDN_URL` | — | R2 CDN 域名，如 `https://cdn.example.com` |
| `OPENAI_API_KEY` | — | OpenAI API Key（AI 摘要/分类功能必填） |
| `ANTHROPIC_API_KEY` | — | Anthropic API Key（AI 深度评论功能必填） |
| `TAVILY_API_KEY` | — | Tavily Search API Key（新闻搜索采集必填） |

**OAuth 回调地址配置：**

- Google：`{CORS_ORIGINS}/auth/google/callback`
- GitHub：`{CORS_ORIGINS}/auth/github/callback`

---

## 项目结构

```
cici-blog/
├── main.py                  # FastAPI 应用入口，注册路由、启动调度器
├── app/
│   ├── api/                 # 路由处理器
│   │   ├── auth.py          # 邮箱注册/登录/登出
│   │   ├── oauth.py         # Google/GitHub OAuth
│   │   ├── posts.py         # 博客文章 CRUD
│   │   ├── comments.py      # 评论（含限流、审核）
│   │   ├── news.py          # AI 新闻浏览
│   │   ├── upload.py        # 图片上传至 R2
│   │   └── agent.py         # RSS 源管理、Agent 手动触发
│   ├── core/
│   │   ├── config.py        # 配置（pydantic-settings，读取 .env）
│   │   ├── database.py      # 异步数据库引擎与会话
│   │   ├── deps.py          # FastAPI 依赖：get_current_user、require_admin
│   │   ├── security.py      # bcrypt 密码哈希、JWT 编解码
│   │   └── rate_limit.py    # 登录限流器
│   ├── models/              # SQLAlchemy ORM 模型
│   │   ├── user.py          # User、OAuthAccount
│   │   ├── blog.py          # BlogPost、Comment
│   │   └── news.py          # NewsArticle、RssSource、AgentRun
│   ├── schemas/             # Pydantic v2 请求/响应模型
│   └── agent/               # AI 新闻采集流水线
│       ├── pipeline.py      # 主流水线：采集 → 去重 → AI 处理 → 存储
│       ├── scheduler.py     # APScheduler，每 4 小时触发一次
│       ├── rss_collector.py # RSS 订阅源采集
│       ├── search_collector.py # Tavily 搜索采集
│       ├── llm_processor.py # GPT-4o-mini 摘要/分类，Claude 深度评论
│       ├── dedup.py         # 基于 URL 的去重
│       └── rss_defaults.py  # 内置默认 RSS 源
├── alembic/                 # 数据库迁移脚本
├── scripts/
│   ├── ensure_database.py   # 自动创建数据库（如不存在）
│   ├── generate_migration.sh # 生成迁移脚本（Linux/macOS）
│   └── generate_migration.bat # 生成迁移脚本（Windows）
└── web/                     # Next.js 前端
    └── src/
        ├── app/             # App Router 页面
        ├── components/      # 可复用组件
        └── lib/
            ├── api.ts       # apiFetch 封装（自动携带 Cookie）
            └── types.ts     # TypeScript 类型定义
```

---

## API 接口

后端运行后可访问 `http://localhost:8000/docs` 查看完整的交互式 API 文档。

| 模块 | 方法 | 路径 | 说明 |
|------|------|------|------|
| 认证 | POST | `/api/v1/auth/register` | 邮箱注册 |
| 认证 | POST | `/api/v1/auth/login` | 邮箱登录 |
| 认证 | POST | `/api/v1/auth/logout` | 退出登录 |
| 认证 | GET | `/api/v1/auth/me` | 获取当前用户信息 |
| OAuth | GET | `/api/v1/auth/oauth/google/url` | 获取 Google 授权链接 |
| OAuth | POST | `/api/v1/auth/oauth/google/callback` | Google 授权回调 |
| OAuth | GET | `/api/v1/auth/oauth/github/url` | 获取 GitHub 授权链接 |
| OAuth | POST | `/api/v1/auth/oauth/github/callback` | GitHub 授权回调 |
| 博客 | GET | `/api/v1/posts` | 文章列表（支持 tag/category/status 过滤） |
| 博客 | GET | `/api/v1/posts/{slug}` | 文章详情 |
| 博客 | POST | `/api/v1/posts` | 创建文章（管理员） |
| 博客 | PUT | `/api/v1/posts/{id}` | 更新文章（管理员） |
| 博客 | DELETE | `/api/v1/posts/{id}` | 删除文章（管理员） |
| 评论 | GET | `/api/v1/posts/{id}/comments` | 获取文章已审核评论 |
| 评论 | POST | `/api/v1/posts/{id}/comments` | 提交评论 |
| 新闻 | GET | `/api/v1/news` | 新闻列表 |
| 新闻 | GET | `/api/v1/news/{slug}` | 新闻详情 |
| 图片 | POST | `/api/v1/upload` | 上传图片至 R2（管理员） |
| 管理 | GET | `/api/v1/admin/rss-sources` | RSS 源列表 |
| 管理 | POST | `/api/v1/admin/agent/trigger` | 手动触发 Agent 流水线 |
| 管理 | GET | `/api/v1/admin/agent/status` | 查看 Agent 运行状态 |
| 健康检查 | GET | `/health` | 服务健康检查 |

---

## 数据库迁移

```bash
# 应用所有待执行的迁移
uv run alembic upgrade head

# 修改模型后，生成新的迁移脚本
./scripts/generate_migration.sh "add some column"
# Windows:
scripts\generate_migration.bat "add some column"

# 回滚一个版本
uv run alembic downgrade -1
```

> 迁移脚本位于 `alembic/versions/`，自动生成后请检查内容再提交。

---

## AI 新闻 Agent

Agent 流水线在应用启动时自动开始调度，每 4 小时执行一次：

1. **采集**：并行从数据库中所有激活的 RSS 订阅源抓取文章，同时通过 Tavily 搜索近期科技资讯
2. **去重**：基于原文 URL 过滤已存在的文章
3. **AI 处理**：
   - GPT-4o-mini 生成 100-200 字中文摘要
   - Claude 生成 500-1500 字深度评论
   - GPT-4o-mini 分类（15 个预设分类）并提取 2-5 个标签
4. **存储**：以 `pending` 状态写入数据库，等待管理员在后台审核发布

管理员可在后台 `/admin/agent` 页面手动触发流水线，或调用 `POST /api/v1/admin/agent/trigger`。

默认内置 RSS 源包括：TechCrunch、The Verge、Hacker News、MIT Technology Review、OpenAI Blog、Google AI Blog、Ars Technica。

---

## 生产部署注意事项

- 将 `ENVIRONMENT` 设为 `production`，此时 `DATABASE_URL` 和 `SECRET_KEY` 为必填项且会校验有效性
- 确保 HTTPS 已启用（Cookie 设置了 `secure=True`）
- 配置反向代理（如 Nginx）转发请求至 Uvicorn
- 前端使用 `npm run build && npm start` 启动，或部署至 Vercel/Cloudflare Pages
- 在 Google Cloud Console / GitHub Developer Settings 中正确填写 OAuth 回调地址
