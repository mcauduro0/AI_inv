// =============================================================================
// Dashboard Page - Investment Committee Intelligence
// =============================================================================
// Main dashboard with institutional grade design showing research overview,
// agent status, and quick actions
// =============================================================================

import { Link } from 'react-router-dom'
import { useResearchStore } from '../stores/researchStore'
import { useAuthStore } from '../stores/authStore'

const quickActions = [
  {
    title: 'Due Diligence',
    description: 'Deep-dive company analysis',
    href: '/research/new?type=due_diligence',
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
      </svg>
    ),
    color: 'from-purple-500 to-pink-500',
  },
  {
    title: 'Idea Generation',
    description: 'Discover new opportunities',
    href: '/research/new?type=idea_generation',
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
      </svg>
    ),
    color: 'from-blue-500 to-cyan-500',
  },
  {
    title: 'Quick Screen',
    description: 'Fast preliminary analysis',
    href: '/research/new?type=quick_screen',
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
      </svg>
    ),
    color: 'from-orange-500 to-yellow-500',
  },
]

const agentStatus = [
  { name: 'Idea Generation Agent', status: 'online', tasks: 0 },
  { name: 'Due Diligence Agent', status: 'online', tasks: 2 },
  { name: 'Portfolio Agent', status: 'online', tasks: 0 },
  { name: 'Macro Agent', status: 'online', tasks: 1 },
]

export default function Dashboard() {
  const { user } = useAuthStore()
  const { tasks } = useResearchStore()

  const recentTasks = tasks.slice(0, 5)
  const runningTasks = tasks.filter((t) => t.status === 'running' || t.status === 'pending')

  return (
    <div className="space-y-8">
      {/* Hero Section */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 border border-slate-800 p-8">
        <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxnIGZpbGw9IiMyMDIwMzAiIGZpbGwtb3BhY2l0eT0iMC40Ij48cGF0aCBkPSJNMzYgMzRoLTJ2LTRoMnY0em0wLTZ2LTRoLTJ2NGgyek0zNCAyNGgtMnYtNGgydjR6Ii8+PC9nPjwvZz48L3N2Zz4=')] opacity-30" />
        <div className="relative">
          <h1 className="text-3xl font-bold text-white mb-2">
            Investment Committee Intelligence
          </h1>
          <p className="text-slate-400 text-lg max-w-2xl">
            Welcome back, {user?.name?.split(' ')[0] || 'Analyst'}. Your AI-powered research team is ready to analyze opportunities.
          </p>

          {/* Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-8">
            <div className="bg-slate-800/50 rounded-xl p-4 backdrop-blur-sm">
              <div className="text-3xl font-bold text-white">{tasks.length}</div>
              <div className="text-sm text-slate-400">Total Research</div>
            </div>
            <div className="bg-slate-800/50 rounded-xl p-4 backdrop-blur-sm">
              <div className="text-3xl font-bold text-accent-blue">{runningTasks.length}</div>
              <div className="text-sm text-slate-400">In Progress</div>
            </div>
            <div className="bg-slate-800/50 rounded-xl p-4 backdrop-blur-sm">
              <div className="text-3xl font-bold text-success">4</div>
              <div className="text-sm text-slate-400">Agents Online</div>
            </div>
            <div className="bg-slate-800/50 rounded-xl p-4 backdrop-blur-sm">
              <div className="text-3xl font-bold text-white">118</div>
              <div className="text-sm text-slate-400">Prompts Available</div>
            </div>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div>
        <h2 className="text-xl font-semibold text-white mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {quickActions.map((action) => (
            <Link
              key={action.title}
              to={action.href}
              className="card-hover group"
            >
              <div className="flex items-start gap-4">
                <div
                  className={`p-3 rounded-xl bg-gradient-to-br ${action.color} text-white group-hover:scale-110 transition-transform`}
                >
                  {action.icon}
                </div>
                <div>
                  <h3 className="font-semibold text-white group-hover:text-accent-blue transition-colors">
                    {action.title}
                  </h3>
                  <p className="text-sm text-slate-400 mt-1">{action.description}</p>
                </div>
              </div>
            </Link>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Research */}
        <div className="lg:col-span-2">
          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold text-white">Recent Research</h2>
              <Link to="/research/history" className="text-sm text-accent-blue hover:text-accent-blue-light">
                View all
              </Link>
            </div>

            {recentTasks.length === 0 ? (
              <div className="text-center py-12">
                <div className="w-16 h-16 mx-auto mb-4 bg-slate-800 rounded-full flex items-center justify-center">
                  <svg className="w-8 h-8 text-slate-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
                <h3 className="text-lg font-medium text-white mb-2">No research yet</h3>
                <p className="text-slate-400 mb-4">Start your first analysis to see results here</p>
                <Link to="/research/new" className="btn-primary inline-flex items-center">
                  <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                  </svg>
                  Start Research
                </Link>
              </div>
            ) : (
              <div className="space-y-3">
                {recentTasks.map((task) => (
                  <Link
                    key={task.id}
                    to={`/research/${task.id}`}
                    className="flex items-center gap-4 p-4 bg-slate-800/50 rounded-lg hover:bg-slate-800 transition-colors"
                  >
                    <div
                      className={`w-2 h-2 rounded-full ${
                        task.status === 'completed'
                          ? 'bg-success'
                          : task.status === 'running'
                          ? 'bg-warning animate-pulse'
                          : task.status === 'failed'
                          ? 'bg-danger'
                          : 'bg-slate-500'
                      }`}
                    />
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-white truncate">
                        {task.ticker || task.theme || 'Research Task'}
                      </p>
                      <p className="text-sm text-slate-400">
                        {task.type.replace('_', ' ').replace(/\b\w/g, (l) => l.toUpperCase())}
                      </p>
                    </div>
                    {task.status === 'running' && (
                      <div className="text-sm text-slate-400">{task.progress}%</div>
                    )}
                    {task.results?.recommendation && (
                      <span
                        className={`badge ${
                          task.results.recommendation === 'buy'
                            ? 'badge-success'
                            : task.results.recommendation === 'sell'
                            ? 'badge-danger'
                            : 'badge-warning'
                        }`}
                      >
                        {task.results.recommendation}
                      </span>
                    )}
                  </Link>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Agent Status */}
        <div>
          <div className="card">
            <h2 className="text-xl font-semibold text-white mb-4">Agent Status</h2>
            <div className="space-y-3">
              {agentStatus.map((agent) => (
                <div
                  key={agent.name}
                  className="flex items-center justify-between p-3 bg-slate-800/50 rounded-lg"
                >
                  <div className="flex items-center gap-3">
                    <div
                      className={`w-2 h-2 rounded-full ${
                        agent.status === 'online' ? 'bg-success' : 'bg-slate-500'
                      }`}
                    />
                    <span className="text-sm text-slate-300">{agent.name}</span>
                  </div>
                  {agent.tasks > 0 && (
                    <span className="badge badge-info">{agent.tasks} tasks</span>
                  )}
                </div>
              ))}
            </div>

            <div className="mt-4 pt-4 border-t border-slate-800">
              <Link
                to="/agents"
                className="text-sm text-accent-blue hover:text-accent-blue-light flex items-center justify-center gap-2"
              >
                Manage Agents
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </Link>
            </div>
          </div>

          {/* Data Sources */}
          <div className="card mt-6">
            <h2 className="text-xl font-semibold text-white mb-4">Data Sources</h2>
            <div className="space-y-2">
              {[
                { name: 'Polygon.io', status: 'connected' },
                { name: 'SEC EDGAR', status: 'connected' },
                { name: 'FMP', status: 'connected' },
                { name: 'Reddit', status: 'connected' },
                { name: 'FRED', status: 'connected' },
              ].map((source) => (
                <div
                  key={source.name}
                  className="flex items-center justify-between py-2"
                >
                  <span className="text-sm text-slate-400">{source.name}</span>
                  <span className="text-xs text-success">Connected</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

// Also export as named export for backwards compatibility
export { Dashboard }
