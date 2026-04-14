import { Link, NavLink, Outlet, useLocation } from "react-router-dom";
import { ThreadsSidebar } from "./ThreadsSidebar";

function Logo({ compact }: { compact?: boolean }) {
  return (
    <Link className="flex items-center gap-3" to="/">
      {!compact ? (
        <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-black text-white shadow-[0_10px_30px_rgba(15,23,42,0.15)]">
          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path d="M4 5V7H6.5C6.9 11.5 7.5 15.5 8 19H10C9.5 15.5 8.9 11.5 8.5 7H13.5C13.9 11.5 14.5 15.5 15 19H17C16.5 15.5 15.9 11.5 15.5 7H18V5H4Z" fill="currentColor" />
            <path d="M12 2C6.48 2 2 6.48 2 12C2 17.52 6.48 22 12 22C17.52 22 22 17.52 22 12" stroke="currentColor" strokeDasharray="2 4" strokeLinecap="round" strokeWidth="1.5" />
          </svg>
        </div>
      ) : null}
      <span className="text-xl font-bold tracking-tight text-slate-950">
        πFlow<span className="ml-1 text-sm font-medium text-slate-400">Agent</span>
      </span>
    </Link>
  );
}

export function AppShell() {
  const location = useLocation();
  const isHome = location.pathname === "/";

  return (
    <div className="flex h-screen flex-col bg-[radial-gradient(circle_at_top,_rgba(226,232,240,0.45),_transparent_32%),linear-gradient(180deg,_#fff_0%,_#f8fafc_100%)]">
      <header className="z-50 flex-shrink-0 border-b border-slate-200/80 bg-white/90 backdrop-blur">
        <div className="flex h-16 items-center justify-between px-6">
          <Logo />

          <nav className="flex items-center gap-3 sm:gap-6">
            <NavLink
              to="/"
              end
              className={({ isActive }) =>
                `text-sm font-medium transition-colors ${
                  isActive
                    ? isHome
                      ? "border-b-2 border-black pb-1 text-black"
                      : "text-black"
                    : "text-slate-500 hover:text-black"
                }`
              }
            >
              首页
            </NavLink>
            <NavLink
              to="/skills"
              className={({ isActive }) =>
                `rounded-none border px-4 py-1.5 text-xs font-bold transition-colors ${
                  isActive
                    ? "border-black bg-black text-white"
                    : isHome
                      ? "border-black text-black hover:bg-black hover:text-white"
                      : "border-slate-300 text-slate-700 hover:border-black hover:text-black"
                }`
              }
            >
              技能中心
            </NavLink>
          </nav>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {isHome ? <ThreadsSidebar /> : null}
        <main className={isHome ? "flex flex-1 flex-col overflow-y-auto custom-scrollbar" : "flex-1 overflow-y-auto custom-scrollbar"}>
          <Outlet />
        </main>
      </div>
    </div>
  );
}
