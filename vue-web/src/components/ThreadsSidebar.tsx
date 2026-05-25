import { Icon } from "@iconify/react";
import { Link, NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import { apiBase } from "../lib/api";
import { useCallback, useEffect, useMemo, useState } from "react";
import { deleteThread, getThreads, type ThreadTitle } from "../lib/api";
import './ThreadsSidebar.css';
function Logo({ compact }: { compact?: boolean }) {
  return (
    <Link className="flex items-center gap-3" to="/">
      {!compact ? (
        <div className="flex h-9 w-9 items-center overflow-hidden rounded-xl bg-black shadow-[0_10px_30px_rgba(15,23,42,0.15)]">
          <img
            alt="πFlow AI"
            className="h-full w-full object-cover"
            src={`${apiBase().replace(/\/+$/, "")}/storage/icon/logo.png`}
          />
        </div>
      ) : null}
      <span className="text-xl font-bold tracking-tight text-slate-950">
        πFlow AI
      </span>
    </Link>
  );
}
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

const menuArr = [{
  id:1,
  title:'编辑任务',
  icon:'fa-solid:edit',
  path:'/editTask'
},
{
  id:2,
  title:'运行历史',
  icon:'fa-solid:history',
  path:'/run-history'
},
{
  id:3,
  title:'算子库',
  icon:'fa-solid:coins',
  path:'/skills'
},
// {
//   id:4,
//   title:'定时调度',
//   icon:'fa-solid:chart-bar',
//   path:'/'
// }
];

export function ThreadsSidebar() {
  const [threads, setThreads] = useState<ThreadTitle[]>([]);
  const [loading, setLoading] = useState(false);
  const [isShow, setIsShow] = useState(true);
  const [activeMenuId, setActiveMenuId] = useState(0);
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
  const navigate = useNavigate();
  // 跳转路由
  const navRouter = useCallback((ids: number, paths:string)=>{
    if (paths) {
      navigate(paths);
    }
    setActiveMenuId(ids);
  }, [navigate]);
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
  // 左边菜单栏显示隐藏的操作方法
  function showMenu(sta:string){
    console.log(sta,'sta')
    if(sta === '1'){
      setIsShow(false);
    }
    if(sta === '0'){
      setIsShow(true);
    }
  }
  return (
    <div className="leftCon">
      
      <aside style={{maxWidth:'280px'}} className="flex w-[280px] flex-shrink-0 flex-col border-r border-slate-200/80 bg-slate-50/85 backdrop-blur">
        <div className="topIcon">
        {isShow ? (<Link className="flex items-center gap-3" to="/">
            
              <div style={{display:'flex',alignItems:'center'}}>
                <img
                  alt="πFlow AI"
                  style={{width:'50px',height:'50px',marginRight:'10px'}}
                  src={`${apiBase().replace(/\/+$/, "")}/storage/icon/logo.png`}
                /> 
                <span className="text-xl font-bold tracking-tight text-slate-950">
                  πFlow AI
                </span>
              </div>
            
          </Link>) : null}
          {isShow ? <Icon icon="fa-solid:align-right" width="16" className="topIcons" onClick={()=>{showMenu('1')}} /> : <Icon icon="fa-solid:align-left" width="16" className="topIcons" onClick={()=>{showMenu('0')}} />}
        </div>
        {isShow ? <div>
          <div className="p-4 pb-3">
            <button
              className="flex w-full items-center justify-center gap-2 rounded-xl bg-black px-4 py-3 text-sm font-semibold text-white transition-colors hover:bg-slate-800"
              onClick={() => {
                setSelectedThreadId("default");
                navigate("/");
              }}
            >
              <Icon icon="ri:add-line" />
              <span>新建对话</span>
            </button>
          </div>
          <div className="menuCon">
            {menuArr.map((item, index) => (
              <div className={`${item.id === activeMenuId ? 'activeOneMenu' : 'oneMenu'}`} key={item.id} onClick={ ()=>{navRouter(item.id,item.path)} }>
                <Icon icon={item.icon} width="16" className="leftIcon" />
                <span className="menuTitle">{item.title}</span>
              </div>
            ))}
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

            <div className="space-y-2" style={{height:'600px'}}>
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
        </div>
        : <div></div>}
      </aside>
    </div>
    
  );
}
