// import { Link, NavLink, Outlet, useLocation } from "react-router-dom";
// import { ToastContainer } from "./Toast";
// import { apiBase } from "../lib/api";
// import { ThreadsSidebar } from "./ThreadsSidebar";

// // function Logo({ compact }: { compact?: boolean }) {
// //   return (
// //     <Link className="flex items-center gap-3" to="/">
// //       {!compact ? (
// //         <div className="flex h-9 w-9 items-center justify-center overflow-hidden rounded-xl bg-black shadow-[0_10px_30px_rgba(15,23,42,0.15)]">
// //           <img
// //             alt="πFlow"
// //             className="h-full w-full object-cover"
// //             src={`${apiBase().replace(/\/+$/, "")}/storage/icon/logo.png`}
// //           />
// //         </div>
// //       ) : null}
// //       <span className="text-xl font-bold tracking-tight text-slate-950">
// //         πFlow
// //       </span>
// //     </Link>
// //   );
// // }

// export function AppShell() {
//   const location = useLocation();
//   const isHome = true;
//   return (
//     <div className="flex h-screen flex-col bg-[radial-gradient(circle_at_top,_rgba(226,232,240,0.45),_transparent_32%),linear-gradient(180deg,_#fff_0%,_#f8fafc_100%)]">
//       <ToastContainer />
//       {/* <header className="z-50 flex-shrink-0 border-b border-slate-200/80 bg-white/90 backdrop-blur">
//         <div className="flex h-16 items-center justify-between px-6">
//           <Logo />

//           <nav className="flex items-center gap-3 sm:gap-6">
//             <NavLink
//               to="/"
//               end
//               className={({ isActive }) =>
//                 `text-sm font-medium transition-colors ${
//                   isActive
//                     ? isHome
//                       ? "border-b-2 border-black pb-1 text-black"
//                       : "text-black"
//                     : "text-slate-500 hover:text-black"
//                 }`
//               }
//             >
//               首页
//             </NavLink>
//             <NavLink
//               to="/skills"
//               className={({ isActive }) =>
//                 `rounded-none border px-4 py-1.5 text-xs font-bold transition-colors ${
//                   isActive
//                     ? "border-black bg-black text-white"
//                     : isHome
//                       ? "border-black text-black hover:bg-black hover:text-white"
//                       : "border-slate-300 text-slate-700 hover:border-black hover:text-black"
//                 }`
//               }
//             >
//               技能中心
//             </NavLink>
//           </nav>
//         </div>
//       </header> */}
      
//       <div className="relative flex flex-1 overflow-hidden">
//         {isHome ? <ThreadsSidebar /> : null}
//         <main className={`relative ${isHome ? "flex flex-1 flex-col overflow-y-auto custom-scrollbar" : "flex-1 overflow-y-auto custom-scrollbar"}`}>
//           <Outlet />
//         </main>
//       </div>
//     </div>





//   );
// }


// 替换新的
import { Outlet, useLocation, NavLink, useNavigate } from "react-router-dom";
import { Icon } from "@iconify/react";
// import { useState, useEffect } from "react"; // 如果暂时没用到可以注释掉
import { ThreadsSidebar } from "./ThreadsSidebar";
import { apiBase } from "../lib/api";

const topMenuItems = [
  { id: 1, title: '编辑任务', icon: 'ri:edit-line', path: '/editTask' },
  { id: 2, title: '运行历史', icon: 'ri:history-line', path: '/run-history' },
  { id: 3, title: '算子库', icon: 'ri:database-line', path: '/skills' },
  { id: 4, title: '工作库', icon: 'ri:calendar-line', path: '/workLib' }
];

export function AppShell() {
  const location = useLocation();
  const navigate = useNavigate();

  // 判断是否在首页（新建对话页）
  const isHomePage = location.pathname === '/';

  return (
    <div className="flex flex-col h-screen bg-slate-50">
      {/* 顶部菜单栏 —— 始终在顶部 */}
      <header className="flex-shrink-0 flex items-center gap-6 border-b border-slate-200 bg-white px-6 py-3 z-10 shadow-sm">
        {/* πFlow Logo - 点击返回首页并触发新对话 */}
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
        <nav className="flex items-center gap-2 ml-4">
            {topMenuItems.map((item) => (
            <NavLink
                key={item.id}
                to={item.path}
                className={({ isActive }) =>
                `flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-all ${
                    isActive
                    ? 'bg-slate-900 text-white shadow-md'
                    : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
                }`
                }
            >
                <Icon icon={item.icon} width="18" />
                <span>{item.title}</span>
            </NavLink>
            ))}
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
        {/* 
           关键修改点：
           1. 将 overflow-y-hidden 改为 overflow-y-auto 
           2. 添加 w-full 确保宽度撑满
        */}
        <main className="flex-1 w-full overflow-y-auto custom-scrollbar bg-slate-50/50">
          <Outlet />
        </main>
      </div>
    </div>
  );
}