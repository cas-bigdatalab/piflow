import { Link, useLocation } from 'react-router-dom';

export default function Header() {
  const location = useLocation();
  const isHome = location.pathname === '/';

  return (
    <header className="border-b border-gray-100 bg-white z-50 flex-shrink-0">
      <div className="px-6 h-16 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Link to="/" className="flex items-center gap-2">
            <div className="w-8 h-8 flex items-center justify-center bg-black rounded-lg">
              <svg
                className="w-5 h-5 text-white"
                fill="none"
                viewBox="0 0 24 24"
                xmlns="http://www.w3.org/2000/svg"
              >
                <path
                  d="M4 5V7H6.5C6.9 11.5 7.5 15.5 8 19H10C9.5 15.5 8.9 11.5 8.5 7H13.5C13.9 11.5 14.5 15.5 15 19H17C16.5 15.5 15.9 11.5 15.5 7H18V5H4Z"
                  fill="currentColor"
                />
                <path
                  d="M12 2C6.48 2 2 6.48 2 12C2 17.52 6.48 22 12 22C17.52 22 22 17.52 22 12"
                  stroke="currentColor"
                  strokeDasharray="2 4"
                  strokeLinecap="round"
                  strokeWidth="1.5"
                />
              </svg>
            </div>
            <span className="text-xl font-bold tracking-tight">
              πFlow<span className="font-medium text-gray-400 text-sm ml-0.5">Agent</span>
            </span>
          </Link>
        </div>
        <nav className="flex items-center gap-8">
          <Link
            to="/"
            className={`text-sm font-medium pb-1 ${
              isHome ? 'border-b-2 border-black' : 'hover:text-gray-500 transition-colors'
            }`}
          >
            首页
          </Link>
          <Link
            to="/skills"
            className={`px-4 py-1.5 border border-black text-xs font-bold transition-colors ${
              isHome
                ? 'hover:bg-black hover:text-white'
                : 'bg-black text-white hover:opacity-80'
            }`}
          >
            技能中心
          </Link>
        </nav>
      </div>
    </header>
  );
}
