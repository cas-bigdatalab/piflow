import { Link, NavLink, Outlet, useLocation } from "react-router-dom";
import { ToastContainer } from "./Toast";
import { apiBase } from "../lib/api";
import { ThreadsSidebar } from "./ThreadsSidebar";

// function Logo({ compact }: { compact?: boolean }) {
//   return (
//     <Link className="flex items-center gap-3" to="/">
//       {!compact ? (
//         <div className="flex h-9 w-9 items-center justify-center overflow-hidden rounded-xl bg-black shadow-[0_10px_30px_rgba(15,23,42,0.15)]">
//           <img
//             alt="πFlow AI"
//             className="h-full w-full object-cover"
//             src={`${apiBase().replace(/\/+$/, "")}/storage/icon/logo.png`}
//           />
//         </div>
//       ) : null}
//       <span className="text-xl font-bold tracking-tight text-slate-950">
//         πFlow AI
//       </span>
//     </Link>
//   );
// }

export function AppShell() {
  const location = useLocation();
  const isHome = true;
  return (
    <div className="flex h-screen flex-col bg-[radial-gradient(circle_at_top,_rgba(226,232,240,0.45),_transparent_32%),linear-gradient(180deg,_#fff_0%,_#f8fafc_100%)]">
      <ToastContainer />
      {/* <header className="z-50 flex-shrink-0 border-b border-slate-200/80 bg-white/90 backdrop-blur">
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
      </header> */}
      
      <div className="relative flex flex-1 overflow-hidden">
        {isHome ? <ThreadsSidebar /> : null}
        <main className={`relative ${isHome ? "flex flex-1 flex-col overflow-y-auto custom-scrollbar" : "flex-1 overflow-y-auto custom-scrollbar"}`}>
          <Outlet />
        </main>
      </div>
    </div>
  );
}
