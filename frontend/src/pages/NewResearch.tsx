import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import toast from 'react-hot-toast'
import { useResearchStore, ResearchType } from '../stores/researchStore'

interface ResearchForm {
  type: ResearchType
  ticker: string
  theme: string
}

const researchTypes = [
  {
    id: 'idea_generation' as ResearchType,
    title: 'Idea Generation',
    description: 'Discover new investment opportunities based on themes, trends, or sectors',
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
      </svg>
    ),
    color: 'from-blue-500 to-cyan-500',
  },
  {
    id: 'due_diligence' as ResearchType,
    title: 'Due Diligence',
    description: 'Deep-dive analysis on a specific company with comprehensive research',
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
      </svg>
    ),
    color: 'from-purple-500 to-pink-500',
  },
  {
    id: 'full_analysis' as ResearchType,
    title: 'Full Analysis',
    description: 'Complete investment analysis including valuation, risks, and recommendation',
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
      </svg>
    ),
    color: 'from-green-500 to-emerald-500',
  },
  {
    id: 'quick_screen' as ResearchType,
    title: 'Quick Screen',
    description: 'Fast preliminary screening to identify if a company warrants deeper analysis',
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
      </svg>
    ),
    color: 'from-orange-500 to-yellow-500',
  },
]

export default function NewResearch() {
  const navigate = useNavigate()
  const { startResearch, isLoading } = useResearchStore()
  const [selectedType, setSelectedType] = useState<ResearchType>('due_diligence')

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ResearchForm>({
    defaultValues: {
      type: 'due_diligence',
    },
  })

  const onSubmit = async (data: ResearchForm) => {
    try {
      const taskId = await startResearch(selectedType, {
        ticker: data.ticker || undefined,
        theme: data.theme || undefined,
      })
      toast.success('Research started!')
      navigate(`/research/${taskId}`)
    } catch (error: any) {
      toast.error(error.message || 'Failed to start research')
    }
  }

  const needsTicker = selectedType === 'due_diligence' || selectedType === 'full_analysis' || selectedType === 'quick_screen'
  const needsTheme = selectedType === 'idea_generation'

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white">New Research</h1>
        <p className="text-slate-400 mt-2">
          Select a research type and provide the necessary inputs to begin analysis
        </p>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-8">
        {/* Research Type Selection */}
        <div>
          <label className="label text-lg mb-4">Select Research Type</label>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {researchTypes.map((type) => (
              <button
                key={type.id}
                type="button"
                onClick={() => setSelectedType(type.id)}
                className={`card-hover text-left transition-all duration-200 ${
                  selectedType === type.id
                    ? 'border-accent-blue ring-1 ring-accent-blue'
                    : ''
                }`}
              >
                <div className="flex items-start gap-4">
                  <div
                    className={`p-3 rounded-xl bg-gradient-to-br ${type.color} text-white`}
                  >
                    {type.icon}
                  </div>
                  <div className="flex-1">
                    <h3 className="font-semibold text-white">{type.title}</h3>
                    <p className="text-sm text-slate-400 mt-1">{type.description}</p>
                  </div>
                  {selectedType === type.id && (
                    <div className="text-accent-blue">
                      <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                      </svg>
                    </div>
                  )}
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Input Fields */}
        <div className="card">
          <h2 className="text-xl font-semibold text-white mb-6">Research Parameters</h2>

          {needsTicker && (
            <div className="mb-6">
              <label htmlFor="ticker" className="label">
                Stock Ticker Symbol
              </label>
              <input
                id="ticker"
                type="text"
                className={errors.ticker ? 'input-error uppercase' : 'input uppercase'}
                placeholder="e.g., AAPL, MSFT, GOOGL"
                {...register('ticker', {
                  required: needsTicker ? 'Ticker is required' : false,
                  pattern: {
                    value: /^[A-Za-z]{1,5}$/,
                    message: 'Invalid ticker format',
                  },
                })}
              />
              {errors.ticker && (
                <p className="mt-1 text-sm text-danger">{errors.ticker.message}</p>
              )}
              <p className="mt-2 text-sm text-slate-500">
                Enter the stock ticker symbol for the company you want to analyze
              </p>
            </div>
          )}

          {needsTheme && (
            <div className="mb-6">
              <label htmlFor="theme" className="label">
                Investment Theme
              </label>
              <input
                id="theme"
                type="text"
                className={errors.theme ? 'input-error' : 'input'}
                placeholder="e.g., AI infrastructure, renewable energy, cybersecurity"
                {...register('theme', {
                  required: needsTheme ? 'Theme is required' : false,
                  minLength: {
                    value: 3,
                    message: 'Theme must be at least 3 characters',
                  },
                })}
              />
              {errors.theme && (
                <p className="mt-1 text-sm text-danger">{errors.theme.message}</p>
              )}
              <p className="mt-2 text-sm text-slate-500">
                Describe the investment theme or trend you want to explore
              </p>
            </div>
          )}

          {/* Advanced Options */}
          <details className="mt-6">
            <summary className="cursor-pointer text-slate-400 hover:text-white transition-colors">
              Advanced Options
            </summary>
            <div className="mt-4 space-y-4 pl-4 border-l border-slate-800">
              <div>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    className="w-4 h-4 rounded border-slate-700 bg-slate-800 text-accent-blue focus:ring-accent-blue"
                    defaultChecked
                  />
                  <span className="ml-2 text-sm text-slate-300">Include SEC filings analysis</span>
                </label>
              </div>
              <div>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    className="w-4 h-4 rounded border-slate-700 bg-slate-800 text-accent-blue focus:ring-accent-blue"
                    defaultChecked
                  />
                  <span className="ml-2 text-sm text-slate-300">Include earnings call transcripts</span>
                </label>
              </div>
              <div>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    className="w-4 h-4 rounded border-slate-700 bg-slate-800 text-accent-blue focus:ring-accent-blue"
                  />
                  <span className="ml-2 text-sm text-slate-300">Include social sentiment analysis</span>
                </label>
              </div>
              <div>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    className="w-4 h-4 rounded border-slate-700 bg-slate-800 text-accent-blue focus:ring-accent-blue"
                  />
                  <span className="ml-2 text-sm text-slate-300">Include insider trading analysis</span>
                </label>
              </div>
            </div>
          </details>
        </div>

        {/* Submit */}
        <div className="flex justify-end gap-4">
          <button
            type="button"
            onClick={() => navigate('/dashboard')}
            className="btn-secondary px-6"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={isLoading}
            className="btn-primary px-8 py-3 flex items-center"
          >
            {isLoading ? (
              <>
                <div className="spinner w-5 h-5 mr-2" />
                Starting...
              </>
            ) : (
              <>
                <svg className="w-5 h-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                Start Research
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  )
}
