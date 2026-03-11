import { Link, useLocation } from 'react-router-dom'
import { BoltIcon, ChartBarIcon, ClockIcon, HomeIcon, MoonIcon, SunIcon, CalendarIcon, HeartIcon, UserIcon, ChatBubbleLeftIcon } from '@heroicons/react/24/outline'

interface LayoutProps {
  children: React.ReactNode
}

export default function Layout({ children }: LayoutProps) {
  const location = useLocation()

  const navItems = [
    { path: '/', label: '首页', icon: HomeIcon },
    { path: '/analysis', label: '分析', icon: ChartBarIcon },
    { path: '/history', label: '历史', icon: ClockIcon },
    { path: '/morning-report', label: '晨间报告', icon: SunIcon },
    { path: '/evening-review', label: '晚间复盘', icon: MoonIcon },
    { path: '/weekly-summary', label: '周度总结', icon: CalendarIcon },
    { path: '/injury-log', label: '伤病记录', icon: HeartIcon },
    { path: '/profile', label: '运动员档案', icon: UserIcon },
    { path: '/chat', label: 'AI 对话', icon: ChatBubbleLeftIcon },
  ]

  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="sticky top-0 z-20 border-b border-slate-200/70 bg-white/85 backdrop-blur-xl">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-2">
              <div className="rounded-xl bg-orange-100 p-2 text-orange-600">
                <BoltIcon className="h-5 w-5" />
              </div>
              <div>
                <h1 className="text-lg font-black tracking-wide text-slate-900">Garmin AI Coach</h1>
                <p className="text-[10px] uppercase tracking-[0.18em] text-slate-500">Performance Console</p>
              </div>
            </div>
            <nav className="flex flex-wrap gap-2">
              {navItems.map((item) => {
                const Icon = item.icon
                const isActive =
                  item.path === '/'
                    ? location.pathname === '/'
                    : location.pathname === item.path || location.pathname.startsWith(`${item.path}/`)
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    className={`flex items-center space-x-1 rounded-xl px-3 py-2 text-sm font-semibold transition-all ${
                      isActive
                        ? 'bg-orange-100 text-orange-700 shadow-sm'
                        : 'text-slate-600 hover:bg-slate-100'
                    }`}
                  >
                    <Icon className="w-5 h-5" />
                    <span>{item.label}</span>
                  </Link>
                )
              })}
            </nav>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {children}
      </main>

      {/* Footer */}
      <footer className="mt-12 border-t border-slate-200 bg-white/80">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <p className="text-center text-sm text-slate-500">
            © 2026 Garmin AI Coach. Train smart, recover smarter.
          </p>
        </div>
      </footer>
    </div>
  )
}
