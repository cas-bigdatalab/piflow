import { Icon } from "@iconify/react";
import { useEffect, useMemo, useState } from "react";
import { deleteThread, getThreads, type ThreadTitle } from "../lib/api";

const DEFAULT_USER_ID = "default_user";

function formatDate(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return new Intl.DateTimeFormat("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  })
    .format(date)
    .replace(/\//g, ".");
}

export function ThreadsSidebar() {
  const [threads, setThreads] = useState<ThreadTitle[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedThreadId, setSelectedThreadId] = useState<string>("default");
  const [error, setError] = useState("");

  const items = useMemo(
    () =>
      threads.map((thread) => ({
        ...thread,
        displayDate: formatDate(thread.updated_at),
      })),
    [threads],
  );

  async function refresh() {
    setLoading(true);
    setError("");
    try {
      const response = await getThreads(DEFAULT_USER_ID);
      setThreads(response.threads || []);
    } catch (err: any) {
      setError(String(err?.message || err));
      setThreads([]);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    refresh().catch(() => {});
  }, []);

  useEffect(() => {
    const onNewChat = () => setSelectedThreadId("default");
    const onSelectThread = (event: Event) => {
      const detail = (event as CustomEvent<{ thread_id?: string }>).detail;
      if (detail?.thread_id) {
        setSelectedThreadId(detail.thread_id);
      }
    };
    const onRefresh = () => {
      refresh().catch(() => {});
    };

    window.addEventListener("flow:new-chat", onNewChat);
    window.addEventListener("flow:select-thread", onSelectThread as EventListener);
    window.addEventListener("flow:threads-refresh", onRefresh);

    return () => {
      window.removeEventListener("flow:new-chat", onNewChat);
      window.removeEventListener("flow:select-thread", onSelectThread as EventListener);
      window.removeEventListener("flow:threads-refresh", onRefresh);
    };
  }, []);

  return (
    <aside className="flex w-[280px] flex-shrink-0 flex-col border-r border-slate-200/80 bg-slate-50/85 backdrop-blur">
      <div className="p-4 pb-3">
        <button
          className="flex w-full items-center justify-center gap-2 rounded-xl bg-black px-4 py-3 text-sm font-semibold text-white transition-colors hover:bg-slate-800"
          onClick={() => {
            setSelectedThreadId("default");
            window.dispatchEvent(new CustomEvent("flow:new-chat"));
          }}
        >
          <Icon icon="ri:add-line" />
          <span>新建对话</span>
        </button>
      </div>

      <div className="mx-4 mb-3 flex items-center justify-between border-b border-slate-200 pb-2">
        <h2 className="text-[11px] font-bold uppercase tracking-[0.24em] text-slate-400">
          对话历史
        </h2>
        <button
          className="text-[11px] text-slate-400 transition-colors hover:text-slate-700"
          onClick={() => refresh().catch(() => {})}
          type="button"
        >
          刷新
        </button>
      </div>

      <div className="flex-1 overflow-y-auto px-3 pb-4 custom-scrollbar">
        {loading ? <div className="px-3 py-6 text-xs text-slate-400">正在加载会话列表…</div> : null}
        {!loading && error ? <div className="px-3 py-6 text-xs text-rose-500">{error}</div> : null}
        {!loading && !error && items.length === 0 ? (
          <div className="rounded-2xl border border-dashed border-slate-200 bg-white/70 px-4 py-6 text-xs text-slate-400">
            还没有历史对话，点击上方按钮开始一次新的任务。
          </div>
        ) : null}

        <div className="space-y-2">
          {items.map((thread) => {
            const active = thread.thread_id === selectedThreadId;
            return (
              <div
                key={thread.thread_id}
                className={
                  active
                    ? "group cursor-pointer rounded-2xl border border-slate-200 bg-white p-3 shadow-[0_8px_30px_rgba(15,23,42,0.06)]"
                    : "group cursor-pointer rounded-2xl border border-transparent p-3 text-slate-500 transition-all hover:border-slate-200 hover:bg-white"
                }
                onClick={() => {
                  setSelectedThreadId(thread.thread_id);
                  window.dispatchEvent(
                    new CustomEvent("flow:select-thread", { detail: { thread_id: thread.thread_id } }),
                  );
                }}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <p
                      className={active ? "truncate font-medium text-slate-900" : "truncate font-medium text-slate-700 group-hover:text-slate-900"}
                      title={thread.title}
                    >
                      {thread.title || "未命名对话"}
                    </p>
                    <p className="mt-1 text-[11px] text-slate-400">{thread.displayDate}</p>
                  </div>

                  <button
                    className="mt-0.5 text-slate-300 transition-colors hover:text-black"
                    title="删除对话"
                    type="button"
                    onClick={(event) => {
                      event.stopPropagation();
                      deleteThread(DEFAULT_USER_ID, thread.thread_id)
                        .then(() => {
                          if (selectedThreadId === thread.thread_id) {
                            setSelectedThreadId("default");
                            window.dispatchEvent(new CustomEvent("flow:new-chat"));
                          }
                          return refresh();
                        })
                        .catch(() => {});
                    }}
                  >
                    <Icon icon="ri:delete-bin-6-line" width="16" />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </aside>
  );
}

