"use client";

import { useEffect, useState } from "react";
import { apiFetch, ApiError } from "@/lib/api";

interface RssSource {
  id: number;
  name: string;
  feed_url: string;
  category: string | null;
  is_active: boolean;
  last_fetched_at: string | null;
}

interface AgentRun {
  id: number;
  started_at: string;
  finished_at: string | null;
  status: string;
  articles_found: number;
  articles_created: number;
  error_log: string | null;
}

interface AgentStatus {
  recent_runs: AgentRun[];
  next_run_time: string | null;
}

export default function AdminAgentPage() {
  const [sources, setSources] = useState<RssSource[]>([]);
  const [status, setStatus] = useState<AgentStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [newName, setNewName] = useState("");
  const [newUrl, setNewUrl] = useState("");
  const [newCategory, setNewCategory] = useState("");
  const [triggering, setTriggering] = useState(false);

  async function loadData() {
    setLoading(true);
    try {
      const [sourcesData, statusData] = await Promise.all([
        apiFetch<RssSource[]>("/admin/rss-sources"),
        apiFetch<AgentStatus>("/admin/agent/status"),
      ]);
      setSources(sourcesData);
      setStatus(statusData);
    } catch {
      // 忽略错误
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  async function handleAddSource() {
    if (!newName || !newUrl) return;
    try {
      await apiFetch("/admin/rss-sources", {
        method: "POST",
        body: JSON.stringify({
          name: newName,
          feed_url: newUrl,
          category: newCategory || null,
        }),
      });
      setNewName("");
      setNewUrl("");
      setNewCategory("");
      loadData();
    } catch (err) {
      alert(err instanceof ApiError ? err.message : "添加失败");
    }
  }

  async function handleDeleteSource(id: number) {
    if (!confirm("确定删除这个 RSS 源吗？")) return;
    try {
      await apiFetch(`/admin/rss-sources/${id}`, { method: "DELETE" });
      loadData();
    } catch (err) {
      alert(err instanceof ApiError ? err.message : "删除失败");
    }
  }

  async function handleToggleSource(source: RssSource) {
    try {
      await apiFetch(`/admin/rss-sources/${source.id}`, {
        method: "PUT",
        body: JSON.stringify({ is_active: !source.is_active }),
      });
      loadData();
    } catch (err) {
      alert(err instanceof ApiError ? err.message : "更新失败");
    }
  }

  async function handleTrigger() {
    setTriggering(true);
    try {
      await apiFetch("/admin/agent/trigger", { method: "POST" });
      alert("Pipeline 已触发，请稍后查看运行记录");
      setTimeout(loadData, 5000);
    } catch (err) {
      alert(err instanceof ApiError ? err.message : "触发失败");
    } finally {
      setTriggering(false);
    }
  }

  function formatTime(dateStr: string | null) {
    if (!dateStr) return "-";
    return new Date(dateStr).toLocaleString("zh-CN");
  }

  if (loading) {
    return (
      <div className="mx-auto max-w-5xl px-4 py-8">
        <p className="text-foreground/50">加载中...</p>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-5xl px-4 py-8 space-y-8">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Agent 控制面板</h1>
        <button
          onClick={handleTrigger}
          disabled={triggering}
          className="rounded-md bg-foreground px-4 py-2 text-sm font-medium text-background hover:opacity-90 disabled:opacity-50"
        >
          {triggering ? "触发中..." : "手动触发 Pipeline"}
        </button>
      </div>

      {/* Agent Status */}
      <section>
        <h2 className="mb-3 text-lg font-semibold">运行状态</h2>
        {status?.next_run_time && (
          <p className="mb-3 text-sm text-foreground/60">
            下次运行: {formatTime(status.next_run_time)}
          </p>
        )}
        {status?.recent_runs.length === 0 ? (
          <p className="text-sm text-foreground/50">暂无运行记录</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="border-b border-foreground/10">
                <tr>
                  <th className="pb-2 font-medium">开始时间</th>
                  <th className="pb-2 font-medium">状态</th>
                  <th className="pb-2 font-medium">发现</th>
                  <th className="pb-2 font-medium">创建</th>
                  <th className="pb-2 font-medium">耗时</th>
                </tr>
              </thead>
              <tbody>
                {status?.recent_runs.map((run) => (
                  <tr key={run.id} className="border-b border-foreground/5">
                    <td className="py-2">{formatTime(run.started_at)}</td>
                    <td className="py-2">
                      <span
                        className={`rounded-full px-2 py-0.5 text-xs ${
                          run.status === "success"
                            ? "bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300"
                            : run.status === "running"
                              ? "bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300"
                              : "bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300"
                        }`}
                      >
                        {run.status}
                      </span>
                    </td>
                    <td className="py-2">{run.articles_found}</td>
                    <td className="py-2">{run.articles_created}</td>
                    <td className="py-2 text-foreground/50">
                      {run.finished_at
                        ? `${Math.round((new Date(run.finished_at).getTime() - new Date(run.started_at).getTime()) / 1000)}s`
                        : "-"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {/* RSS Sources */}
      <section>
        <h2 className="mb-3 text-lg font-semibold">RSS 订阅源</h2>

        <div className="mb-4 flex gap-2">
          <input
            placeholder="名称"
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            className="rounded-md border border-foreground/20 bg-background px-3 py-1.5 text-sm"
          />
          <input
            placeholder="Feed URL"
            value={newUrl}
            onChange={(e) => setNewUrl(e.target.value)}
            className="flex-1 rounded-md border border-foreground/20 bg-background px-3 py-1.5 text-sm"
          />
          <input
            placeholder="分类"
            value={newCategory}
            onChange={(e) => setNewCategory(e.target.value)}
            className="w-24 rounded-md border border-foreground/20 bg-background px-3 py-1.5 text-sm"
          />
          <button
            onClick={handleAddSource}
            className="rounded-md bg-foreground px-3 py-1.5 text-sm text-background hover:opacity-90"
          >
            添加
          </button>
        </div>

        {sources.length === 0 ? (
          <p className="text-sm text-foreground/50">暂无 RSS 源</p>
        ) : (
          <div className="space-y-2">
            {sources.map((s) => (
              <div
                key={s.id}
                className="flex items-center justify-between rounded-md border border-foreground/10 px-4 py-2"
              >
                <div>
                  <span className={`font-medium ${!s.is_active ? "text-foreground/40" : ""}`}>
                    {s.name}
                  </span>
                  <span className="ml-2 text-xs text-foreground/40">
                    {s.category || "未分类"}
                  </span>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => handleToggleSource(s)}
                    className="text-xs text-foreground/50 hover:text-foreground"
                  >
                    {s.is_active ? "禁用" : "启用"}
                  </button>
                  <button
                    onClick={() => handleDeleteSource(s.id)}
                    className="text-xs text-red-500 hover:text-red-700"
                  >
                    删除
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
