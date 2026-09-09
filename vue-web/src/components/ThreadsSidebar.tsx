import { Icon } from "@iconify/react";
import { NavLink, useLocation, useNavigate } from "react-router-dom";
import { getLogin, iconBase } from "../lib/api";
import { useCallback, useEffect, useMemo, useState } from "react";
import { deleteThread, getThreads, type ThreadTitle } from "../lib/api";
import { appConfig } from "../config/appConfig";
import './ThreadsSidebar.css';

function getUserId() {
  return localStorage.getItem('userId') || '';
}

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

// 主导航菜单项类型，支持 children 嵌套
interface MenuChild {
  title: string;
  path: string;
  icon?: string;
}
interface MenuItem {
  id: number;
  title: string;
  icon: string;
  path?: string; // 带 children 的父级可以没有 path
  children?: MenuChild[];
  // 分组：设为 true 时在该项之前渲染分隔线
  groupStart?: boolean;
}

// 依据图片样式排列的左侧主导航菜单
const menuArr: MenuItem[] = [
  { id: 1, title: '智能编排', icon: 'ri:sparkling-2-line', path: '/' },
  { id: 2, title: '任务管理', icon: 'ri:node-tree', path: '/editTask' },
  // { id: 2, title: '自动化任务', icon: 'ri:time-line', path: '/automationTasks' },
  { id: 3, title: '运行历史', icon: 'ri:history-line', path: '/run-history' },
  {
    id: 4,
    title: '数据管理',
    icon: 'ri:folder-2-line',
    groupStart: true,
    children: [
      { title: '我的数据', path: '/dataMan', icon: 'ri:file-list-line' },
      { title: '数据连接', path: '/dataMan-connections', icon: 'ri:links-line' },
    ],
  },
  { id: 5, title: '算子管理', icon: 'ri:apps-2-line', path: '/skills' },
  { id: 6, title: '工作流模板管理', icon: 'ri:layout-2-line', path: '/workLib' },
  { id: 7, title: '组织管理', icon: 'ri:building-line', groupStart: true, path: '/UserManagement' },
];

export function ThreadsSidebar() {
  const [threads, setThreads] = useState<ThreadTitle[]>([]);
  const [loading, setLoading] = useState(false);
  const [isShow, setIsShow] = useState(true);
  const [openMenuId, setOpenMenuId] = useState<number | null>(null);
  const [selectedThreadId, setSelectedThreadId] = useState<string>("default");
  const [error, setError] = useState("");
  const [isSending, setIsSending] = useState(false);

  const navigate = useNavigate();
  const location = useLocation();

  const userName = localStorage.getItem("userName") || "李明";
  const userInitial = userName.slice(0, 1);

  const items = useMemo(
    () =>
      threads.map((thread) => ({
        ...thread,
        displayDate: formatDate(thread.updated_at),
      })),
    [threads],
  );

  // 页面加载时先判断URL是否有传参ylk_token,有则保存到本地并移除URL参数，否则请求登录接口
  useEffect(() => {
    let cancelled = false;
    const init = async () => {
      const params = new URLSearchParams(window.location.search);
      const userId = params.get('userId');
      const userNameParam = params.get('userName');
      const token = params.get('token');
      const ylk_token = params.get('ylk_token');
      const ylk_toolId = params.get('ylk_toolId');
      const ylk_desktopId = params.get('ylk_desktopId');
      if (ylk_token) {
        localStorage.setItem('token', token);
        localStorage.setItem('userId', userId);
        localStorage.setItem('userName', userNameParam);
        localStorage.setItem('ylk_token', ylk_token);
        localStorage.setItem('ylk_toolId', ylk_toolId);
        localStorage.setItem('ylk_desktopId', ylk_desktopId);

        // 从URL中移除token、userId、userName参数
        params.delete('token');
        params.delete('userId');
        params.delete('userName');
        params.delete('ylk_token');
        params.delete('ylk_toolId');
        params.delete('ylk_desktopId');
        const newSearch = params.toString();
        const newUrl = newSearch
          ? `${window.location.pathname}?${newSearch}${window.location.hash}`
          : `${window.location.pathname}${window.location.hash}`;
        window.history.replaceState({}, document.title, newUrl);
      } else {
        try {
          let loginParams = { username: appConfig.username, password: appConfig.password };
          let loginRes = await getLogin(loginParams);
          localStorage.setItem('token', loginRes.access_token);
          localStorage.setItem('userId', loginRes.user_id);
          localStorage.setItem('userName', loginRes.user_name);
          console.log('登录了');
        } catch (error) {
          console.error('登录失败:', error);
        }
      }
      if (!cancelled) {
        await refresh();
      }
    };

    init();
    return () => { cancelled = true; };
  }, []);

  async function refresh() {
    setLoading(true);
    setError("");
    try {
      const response = await getThreads(getUserId());
      setThreads(response.threads || []);
    } catch (err: any) {
      setError(String(err?.message || err));
      setThreads([]);
    } finally {
      setLoading(false);
    }
  }

  // 主导航点击：带 children 的项切换展开，其余直接跳转
  const handleMenuClick = useCallback((item: MenuItem) => {
    if (item.children) {
      setOpenMenuId((prev) => (prev === item.id ? null : item.id));
      return;
    }
    if (item.path) {
      navigate(item.path);
    }
  }, [navigate]);

  // 判断菜单项是否处于激活态
  const isMenuActive = useCallback((item: MenuItem) => {
    if (item.path) {
      return location.pathname === item.path;
    }
    return item.children?.some((child) => location.pathname.startsWith(child.path)) ?? false;
  }, [location.pathname]);

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
    const onSendingStart = () => setIsSending(true);
    const onSendingEnd = () => setIsSending(false);

    // 新增：监听折叠侧边栏事件
    const onSidebarCollapse = () => {
      setIsShow(false);
    };

    window.addEventListener("flow:new-chat", onNewChat);
    window.addEventListener("flow:select-thread", onSelectThread as EventListener);
    window.addEventListener("flow:threads-refresh", onRefresh);
    window.addEventListener("flow:sending-start", onSendingStart);
    window.addEventListener("flow:sending-end", onSendingEnd);
    //增加页面监控左侧菜单栏折叠
    window.addEventListener("flow:sidebar-collapse", onSidebarCollapse);

    return () => {
      window.removeEventListener("flow:new-chat", onNewChat);
      window.removeEventListener("flow:select-thread", onSelectThread as EventListener);
      window.removeEventListener("flow:threads-refresh", onRefresh);
      window.removeEventListener("flow:sending-start", onSendingStart);
      window.removeEventListener("flow:sending-end", onSendingEnd);
      //增加返回页面监控左侧菜单栏折叠
      window.removeEventListener("flow:sidebar-collapse", onSidebarCollapse)
    };
  }, []);

  return (
    <aside
      className={`relative z-20 flex h-screen flex-shrink-0 flex-col border-r border-slate-200/80 bg-[#f7f7f9] backdrop-blur transition-all duration-300 ${isShow ? 'w-[260px]' : 'w-[64px]'}`}
    >
      {isSending && (
        <div className="absolute inset-0 z-[100] cursor-not-allowed bg-white/20" />
      )}

      {/* 顶部：Logo + 折叠按钮 */}
      <div className={`flex items-center ${isShow ? 'justify-between px-4' : 'justify-center px-2'} pt-4 pb-3`}>
        {isShow && (
          <div
            className="flex items-center gap-2 cursor-pointer"
            onClick={() => {
              navigate("/");
              window.dispatchEvent(new CustomEvent("flow:new-chat"));
            }}
          >
            <div className="flex h-8 w-8 items-center justify-center overflow-hidden rounded-lg">
              <img
                alt="πFlow"
                className="h-full w-full object-cover"
                src={`${iconBase().replace(/\/+$/, "")}/storage/icon/logo.png`}
              />
            </div>
            <span className="text-xl font-bold tracking-tight text-slate-950">
              πFlow
            </span>
          </div>
        )}
        <button
          type="button"
          className="cursor-pointer text-slate-400 transition-colors hover:text-slate-700 outline-none"
          onClick={() => setIsShow((v) => !v)}
          title={isShow ? "收起菜单" : "展开菜单"}
        >
          <Icon
            icon={isShow ? "ri:arrow-left-s-line" : "ri:arrow-right-s-line"}
            width="20"
          />
        </button>
      </div>

      {/* 主导航菜单 */}
      <nav className={`flex flex-col gap-1 ${isShow ? 'px-3' : 'px-2'} pb-2`}>
        {menuArr.map((item) => {
          const active = isMenuActive(item);
          const hasChildren = !!item.children;
          const isOpen = openMenuId === item.id;
          return (
            <div key={item.id}>
              {item.groupStart && <div className="my-2 border-t border-slate-200/70" />}
              <button
                type="button"
                onClick={() => handleMenuClick(item)}
                title={item.title}
                className={`
                  flex w-full items-center rounded-xl text-sm font-medium transition-colors outline-none
                  ${isShow ? 'gap-3 px-3 py-2.5' : 'justify-center px-0 py-2.5'}
                  ${active
                    ? 'bg-emerald-50 text-emerald-700'
                    : 'text-slate-600 hover:bg-slate-200/60 hover:text-slate-900'}
                `}
              >
                <Icon icon={item.icon} width="18" className="flex-shrink-0" />
                {isShow && <span className="flex-1 truncate text-left">{item.title}</span>}
                {isShow && hasChildren && (
                  <Icon
                    icon="ri:arrow-right-s-line"
                    width="16"
                    className={`flex-shrink-0 text-slate-400 transition-transform duration-200 ${isOpen ? 'rotate-90' : ''}`}
                  />
                )}
              </button>

              {/* 子菜单 */}
              {isShow && hasChildren && isOpen && (
                <div className="mt-1 flex flex-col gap-1 pl-9">
                  {item.children!.map((child) => (
                    <NavLink
                      key={child.path}
                      to={child.path}
                      className={({ isActive }) => `
                        flex items-center gap-2 rounded-lg px-3 py-2 text-sm transition-colors
                        ${isActive
                          ? 'bg-emerald-50 text-emerald-700 font-medium'
                          : 'text-slate-500 hover:bg-slate-200/60 hover:text-slate-900'}
                      `}
                    >
                      {child.icon && <Icon icon={child.icon} width="15" />}
                      <span className="truncate">{child.title}</span>
                    </NavLink>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </nav>

      {/* 对话历史：位于主导航菜单下方 */}
      {isShow && (
        <div className="flex min-h-0 flex-1 flex-col overflow-hidden">
          <div className="mx-4 mb-2 mt-2 flex items-center justify-between border-t border-slate-200 pt-3">
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
            {loading ? (
              <div className="px-3 py-6 text-xs text-slate-400">正在加载会话列表…</div>
            ) : null}
            {!loading && error ? (
              <div className="px-3 py-6 text-xs text-rose-500">{error}</div>
            ) : null}
            {!loading && !error && items.length === 0 ? (
              <div className="rounded-2xl border border-dashed border-slate-200 bg-white/70 px-4 py-6 text-xs text-slate-400">
                还没有历史对话，点击「智能编排」开始一次新的任务。
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
                      navigate("/");
                      setTimeout(() => {
                        window.dispatchEvent(
                          new CustomEvent("flow:select-thread", { detail: { thread_id: thread.thread_id } }),
                        );
                      }, 100);
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
                          deleteThread(getUserId(), thread.thread_id)
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
      )}

      {/* 折叠状态下用弹性占位，把底部用户信息推到底 */}
      {!isShow && <div className="flex-1" />}

      {/* 底部：搜索 + 用户信息 */}
      <div className="mt-auto border-t border-slate-200/70">
        {isShow ? (
          <>
            <button
              type="button"
              className="flex w-full items-center justify-between px-5 py-3 text-sm text-slate-500 transition-colors hover:text-slate-800"
            >
              <span className="flex items-center gap-2">
                <Icon icon="ri:search-line" width="16" />
                <span>搜索与命令</span>
              </span>
              <span className="rounded border border-slate-300 px-1.5 py-0.5 text-[11px] text-slate-400">⌘ K</span>
            </button>
            {/* onClick={() => navigate('/PersonalCenter')} */}
            <button
              type="button"
              
              className="flex w-full items-center gap-3 px-4 py-3 transition-colors hover:bg-slate-200/50"
            >
              <div className="flex h-9 w-9 items-center justify-center rounded-full bg-slate-900 text-sm font-semibold text-white">
                {userInitial}
              </div>
              <div className="min-w-0 text-left">
                <div className="truncate text-sm font-medium leading-tight text-slate-900">{userName}</div>
                <div className="truncate text-xs leading-tight text-slate-500">组织管理员</div>
              </div>
            </button>
          </>
        ) : (
          <button
            type="button"
            onClick={() => navigate('/PersonalCenter')}
            title={userName}
            className="flex w-full items-center justify-center py-3 transition-colors hover:bg-slate-200/50"
          >
            <div className="flex h-9 w-9 items-center justify-center rounded-full bg-slate-900 text-sm font-semibold text-white">
              {userInitial}
            </div>
          </button>
        )}
      </div>
    </aside>
  );
}
