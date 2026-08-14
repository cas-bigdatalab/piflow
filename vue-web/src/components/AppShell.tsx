import { useState, useRef, useEffect } from "react"; // 引入 hooks
import { Outlet, useLocation, NavLink, useNavigate } from "react-router-dom";
import { Icon } from "@iconify/react";
import { ThreadsSidebar } from "./ThreadsSidebar";
import { apiBase } from "../lib/api";

// 定义菜单项类型，支持 children 嵌套
interface MenuItem {
  id: number;
  title: string;
  icon: string;
  path?: string; // 下拉菜单的父级可能不需要 path
  children?: { title: string; path: string; icon?: string }[];
}

const topMenuItems: MenuItem[] = [
  { id: 1, title: '新建对话', icon: 'ri:add-line', path: '/' },
  { id: 2, title: '编辑任务', icon: 'ri:edit-line', path: '/editTask' },
  { id: 3, title: '运行历史', icon: 'ri:history-line', path: '/run-history' },
  { 
    id: 6, 
    title: '数据管理', 
    icon: 'ri:database-2-line', // 换了个更贴切的图标
    children: [
      { title: '我的数据', path: '/dataMan', icon: 'ri:file-list-line' },
      { title: '数据连接', path: '/dataMan-connections', icon: 'ri:links-line' }
    ]
  },
  { id: 4, title: '算子库', icon: 'ri:database-line', path: '/skills' },
  // { id: 5, title: '工作库', icon: 'ri:calendar-line', path: '/workLib' },
  // 修改点：数据管理增加 children
];

export function AppShell() {
  const location = useLocation();
  const navigate = useNavigate();
  
  // 状态管理：当前打开的下拉菜单 ID (null 表示没有打开)
  const [openDropdownId, setOpenDropdownId] = useState<number | null>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const isHomePage = location.pathname === '/';

  // 点击外部关闭下拉菜单的逻辑
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setOpenDropdownId(null);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleMenuClick = (item: MenuItem, e: React.MouseEvent) => {
    if (item.children) {
      e.preventDefault(); // 阻止默认跳转
      // 如果点击的是当前已打开的菜单，则关闭；否则打开
      setOpenDropdownId(openDropdownId === item.id ? null : item.id);
    } else if (item.path) {
      navigate(item.path);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-slate-50">
      {/* 顶部菜单栏 */}
      <header className="flex-shrink-0 flex items-center gap-6 border-b border-slate-200 bg-white px-6 py-3 z-50 shadow-sm relative">
        {/* Logo */}
        <div
          className="flex items-center gap-3 cursor-pointer hover:opacity-80 transition-opacity"
          onClick={() => {
            navigate("/");
            window.dispatchEvent(new CustomEvent("flow:new-chat"));
          }}
        >
          <img
            alt="πFlow"
            style={{ width: '28px', height: '28px' }}
            src={`${apiBase().replace(/\/+$/, "")}/storage/icon/logo.png`}
          />
          <span className="text-xl font-bold tracking-tight text-slate-950">
            πFlow
          </span>
        </div>

        {/* 导航菜单项 */}
        <nav className="flex items-center gap-2 ml-4" ref={dropdownRef}>
          {topMenuItems.map((item) => {
            // 判断是否是当前激活的路由（包括子路由）
            const isActive = item.path 
              ? location.pathname === item.path 
              : item.children?.some(child => location.pathname.startsWith(child.path));

            // 判断是否是带有下拉菜单的项
            const hasDropdown = !!item.children;
            const isDropdownOpen = openDropdownId === item.id;

            return (
              <div key={item.id} className="relative group">
                {/* 菜单按钮 */}
                <button
                  onClick={(e) => handleMenuClick(item, e)}
                  className={`
                    flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-all outline-none
                    ${isActive && !hasDropdown ? 'bg-slate-900 text-white shadow-md' : ''}
                    ${hasDropdown && isDropdownOpen ? 'bg-slate-100 text-slate-900' : ''}
                    ${!isActive && !isDropdownOpen ? 'text-slate-600 hover:bg-slate-100 hover:text-slate-900' : ''}
                  `}
                >
                  <Icon icon={item.icon} width="18" />
                  <span>{item.title}</span>
                  {/* 如果有子菜单，显示一个小箭头 */}
                  {hasDropdown && (
                    <Icon 
                      icon="ri:arrow-down-s-line" 
                      width="16" 
                      className={`transition-transform duration-200 ${isDropdownOpen ? 'rotate-180' : ''}`} 
                    />
                  )}
                </button>

                {/* 下拉菜单面板 */}
                {hasDropdown && isDropdownOpen && (
                  <div className="absolute top-full left-0 mt-2 w-48 bg-white rounded-lg shadow-xl border border-slate-100 py-1 z-50 animate-in fade-in zoom-in-95 duration-100">
                    {item.children?.map((child, index) => (
                      <NavLink
                        key={index}
                        to={child.path}
                        onClick={() => setOpenDropdownId(null)} // 点击子项后关闭菜单
                        className={({ isActive }) => `
                          flex items-center gap-3 px-4 py-2.5 text-sm transition-colors
                          ${isActive 
                            ? 'bg-slate-50 text-blue-600 font-medium' 
                            : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'}
                        `}
                      >
                        {child.icon && <Icon icon={child.icon} width="16" />}
                        <span>{child.title}</span>
                      </NavLink>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </nav>
      </header>

      {/* 主体内容区 */}
      <div className="flex flex-1 overflow-hidden relative">
        {/* 左侧边栏：仅在首页显示 */}
        {isHomePage && (
          <aside className="flex-shrink-0 h-full border-r border-slate-200 bg-white">
            <ThreadsSidebar />
          </aside>
        )}

        {/* 右侧主内容区 */}
        <main className="flex-1 w-full overflow-y-auto custom-scrollbar bg-slate-50/50">
          <Outlet />
        </main>
      </div>
    </div>
  );
}