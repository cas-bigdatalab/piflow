import { Outlet } from "react-router-dom";
import { ThreadsSidebar } from "./ThreadsSidebar";

export function AppShell() {
  return (
    <div className="flex h-screen overflow-hidden bg-slate-50">
      {/* 左侧全局导航栏：主菜单 + 对话历史 + 用户信息 */}
      <ThreadsSidebar />

      {/* 右侧主内容区 */}
      <main className="flex-1 w-full overflow-y-auto custom-scrollbar bg-slate-50/50">
        <Outlet />
      </main>
    </div>
  );
}
