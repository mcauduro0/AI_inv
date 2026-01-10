import { useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useResearchStore } from '../stores/researchStore'

export default function ResearchView() {
  const { taskId } = useParams<{ taskId: string }>()
  const navigate = useNavigate()
  const { tasks, activeTask, setActiveTask, getTask } = useResearchStore()

  useEffect(() => {
    if (taskId) {
      const task = getTask(taskId)
      if (task) {
        setActiveTask(task)
      }
    }
  }, [taskId, tasks])

  if (!activeTask) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="spinner w-12 h-12 mx-auto mb-4" />
          <p className="text-slate-400">Loading research...</p>
        </div>
      </div>
    )
  }

  const isRunning = activeTask.status === 'running' || activeTask.status === 'pending'
  const isCompleted = activeTask.status === 'completed'
  const isFailed = activeTask.status === 'failed'

  return (
    <div className="max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <button
              onClick={() => navigate('/dashboard')}
              className="text-slate-400 hover:text-white transition-colors"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
              </svg>
            </button>
            <h1 className="text-2xl font-bold text-white">
              {activeTask.ticker ? `${activeTask.ticker} Analysis` : activeTask.theme || 'Research'}
            </h1>
            <span
              className={`badge ${
                isRunning
                  ? 'badge-warning'
                  : isCompleted
                  ? 'badge-success'
                  : isFailed
                  ? 'badge-danger'
                  : 'badge-info'
              }`}
            >
              {activeTask.status}
            </span>
          </div>
          <p className="text-slate-400">
            {activeTask.type.replace('_', ' ').replace(/\b\w/g, (l) => l.toUpperCase())}
          </p>
        </div>

        {isCompleted && (
          <div className="flex gap-3">
            <button className="btn-secondary flex items-center">
              <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
              Export PDF
            </button>
            <button className="btn-primary flex items-center">
              <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" />
              </svg>
              Share
            </button>
          </div>
        )}
      </div>

      {/* Progress Section (when running) */}
      {isRunning && (
        <div className="card mb-8">
          <div className="flex items-center gap-4 mb-4">
            <div className="spinner w-8 h-8" />
            <div>
              <h3 className="font-semibold text-white">Research in Progress</h3>
              <p className="text-slate-400 text-sm">{activeTask.currentStep}</p>
            </div>
          </div>
          <div className="w-full bg-slate-800 rounded-full h-2">
            <div
              className="bg-accent-blue h-2 rounded-full transition-all duration-500"
              style={{ width: `${activeTask.progress}%` }}
            />
          </div>
          <p className="text-right text-sm text-slate-500 mt-2">{activeTask.progress}% complete</p>
        </div>
      )}

      {/* Error Section (when failed) */}
      {isFailed && (
        <div className="card border-danger/50 bg-danger/10 mb-8">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-danger/20 rounded-full">
              <svg className="w-6 h-6 text-danger" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div>
              <h3 className="font-semibold text-white">Research Failed</h3>
              <p className="text-slate-400 text-sm">{activeTask.error || 'An unexpected error occurred'}</p>
            </div>
            <button
              onClick={() => navigate('/research/new')}
              className="btn-primary ml-auto"
            >
              Try Again
            </button>
          </div>
        </div>
      )}

      {/* Results Section (when completed) */}
      {isCompleted && activeTask.results && (
        <div className="space-y-6">
          {/* Summary Card */}
          <div className="card">
            <div className="flex items-start justify-between mb-4">
              <h2 className="text-xl font-semibold text-white">Executive Summary</h2>
              {activeTask.results.recommendation && (
                <span
                  className={`badge text-sm px-4 py-1 ${
                    activeTask.results.recommendation === 'buy'
                      ? 'bg-success/20 text-success'
                      : activeTask.results.recommendation === 'sell'
                      ? 'bg-danger/20 text-danger'
                      : 'bg-warning/20 text-warning'
                  }`}
                >
                  {activeTask.results.recommendation.toUpperCase()}
                </span>
              )}
            </div>
            <p className="text-slate-300 leading-relaxed">{activeTask.results.summary}</p>

            {/* Score */}
            {activeTask.results.score !== undefined && (
              <div className="mt-6 flex items-center gap-4">
                <div className="text-center">
                  <div className="text-4xl font-bold gradient-text">{activeTask.results.score}</div>
                  <div className="text-sm text-slate-500">Investment Score</div>
                </div>
                <div className="flex-1 h-3 bg-slate-800 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full ${
                      activeTask.results.score >= 70
                        ? 'bg-success'
                        : activeTask.results.score >= 50
                        ? 'bg-warning'
                        : 'bg-danger'
                    }`}
                    style={{ width: `${activeTask.results.score}%` }}
                  />
                </div>
              </div>
            )}
          </div>

          {/* Key Metrics */}
          {activeTask.results.metrics && (
            <div className="card">
              <h2 className="text-xl font-semibold text-white mb-4">Key Metrics</h2>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {Object.entries(activeTask.results.metrics).map(([key, value]) => (
                  <div key={key} className="bg-slate-800/50 rounded-lg p-4">
                    <div className="text-2xl font-bold text-white">
                      {typeof value === 'number' ? value.toFixed(2) : value}
                    </div>
                    <div className="text-sm text-slate-400 capitalize">
                      {key.replace(/_/g, ' ')}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Analysis Sections */}
          <div className="space-y-4">
            {activeTask.results.sections.map((section, index) => (
              <div key={index} className="card">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-lg font-semibold text-white">{section.title}</h3>
                  {section.confidence !== undefined && (
                    <span className="text-sm text-slate-500">
                      {Math.round(section.confidence * 100)}% confidence
                    </span>
                  )}
                </div>
                <p className="text-slate-300 leading-relaxed">{section.content}</p>
              </div>
            ))}
          </div>

          {/* Sources */}
          {activeTask.results.sources.length > 0 && (
            <div className="card">
              <h2 className="text-xl font-semibold text-white mb-4">Sources</h2>
              <div className="space-y-2">
                {activeTask.results.sources.map((source, index) => (
                  <a
                    key={index}
                    href={source.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-3 p-3 bg-slate-800/50 rounded-lg hover:bg-slate-800 transition-colors"
                  >
                    <span className="badge badge-info">{source.type}</span>
                    <span className="text-slate-300 flex-1">{source.title}</span>
                    <svg className="w-4 h-4 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                    </svg>
                  </a>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
