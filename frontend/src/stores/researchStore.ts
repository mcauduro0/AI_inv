import { create } from 'zustand'

export type ResearchStatus = 'idle' | 'pending' | 'running' | 'completed' | 'failed'
export type ResearchType = 'idea_generation' | 'due_diligence' | 'full_analysis' | 'quick_screen'

export interface ResearchTask {
  id: string
  type: ResearchType
  status: ResearchStatus
  ticker?: string
  theme?: string
  progress: number
  currentStep: string
  results?: ResearchResult
  error?: string
  createdAt: string
  updatedAt: string
}

export interface ResearchResult {
  summary: string
  score?: number
  recommendation?: 'buy' | 'hold' | 'sell' | 'pass'
  sections: {
    title: string
    content: string
    confidence?: number
  }[]
  sources: {
    title: string
    url: string
    type: string
  }[]
  metrics?: Record<string, any>
}

interface ResearchState {
  tasks: ResearchTask[]
  activeTask: ResearchTask | null
  isLoading: boolean
  
  // Actions
  startResearch: (type: ResearchType, params: { ticker?: string; theme?: string }) => Promise<string>
  getTask: (taskId: string) => ResearchTask | undefined
  setActiveTask: (task: ResearchTask | null) => void
  updateTaskProgress: (taskId: string, progress: number, step: string) => void
  completeTask: (taskId: string, results: ResearchResult) => void
  failTask: (taskId: string, error: string) => void
  clearTasks: () => void
}

const API_URL = import.meta.env.VITE_API_URL || '/api'

export const useResearchStore = create<ResearchState>((set, get) => ({
  tasks: [],
  activeTask: null,
  isLoading: false,

  startResearch: async (type, params) => {
    set({ isLoading: true })
    
    const taskId = `task_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    const newTask: ResearchTask = {
      id: taskId,
      type,
      status: 'pending',
      ticker: params.ticker,
      theme: params.theme,
      progress: 0,
      currentStep: 'Initializing research...',
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    }

    set((state) => ({
      tasks: [newTask, ...state.tasks],
      activeTask: newTask,
      isLoading: false,
    }))

    // Start the actual research via API
    try {
      const response = await fetch(`${API_URL}/research/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ task_id: taskId, type, ...params }),
      })

      if (!response.ok) {
        throw new Error('Failed to start research')
      }

      set((state) => ({
        tasks: state.tasks.map((t) =>
          t.id === taskId ? { ...t, status: 'running' } : t
        ),
      }))
    } catch (error) {
      // For demo purposes, simulate progress if API is not available
      simulateResearchProgress(taskId, set, get)
    }

    return taskId
  },

  getTask: (taskId) => {
    return get().tasks.find((t) => t.id === taskId)
  },

  setActiveTask: (task) => {
    set({ activeTask: task })
  },

  updateTaskProgress: (taskId, progress, step) => {
    set((state) => ({
      tasks: state.tasks.map((t) =>
        t.id === taskId
          ? { ...t, progress, currentStep: step, updatedAt: new Date().toISOString() }
          : t
      ),
      activeTask:
        state.activeTask?.id === taskId
          ? { ...state.activeTask, progress, currentStep: step }
          : state.activeTask,
    }))
  },

  completeTask: (taskId, results) => {
    set((state) => ({
      tasks: state.tasks.map((t) =>
        t.id === taskId
          ? {
              ...t,
              status: 'completed',
              progress: 100,
              results,
              updatedAt: new Date().toISOString(),
            }
          : t
      ),
      activeTask:
        state.activeTask?.id === taskId
          ? { ...state.activeTask, status: 'completed', progress: 100, results }
          : state.activeTask,
    }))
  },

  failTask: (taskId, error) => {
    set((state) => ({
      tasks: state.tasks.map((t) =>
        t.id === taskId
          ? { ...t, status: 'failed', error, updatedAt: new Date().toISOString() }
          : t
      ),
    }))
  },

  clearTasks: () => {
    set({ tasks: [], activeTask: null })
  },
}))

// Simulate research progress for demo
function simulateResearchProgress(
  taskId: string,
  set: any,
  _get: any
) {
  const steps = [
    { progress: 10, step: 'Gathering market data...' },
    { progress: 25, step: 'Analyzing financial statements...' },
    { progress: 40, step: 'Evaluating competitive landscape...' },
    { progress: 55, step: 'Assessing management quality...' },
    { progress: 70, step: 'Identifying key risks...' },
    { progress: 85, step: 'Generating investment thesis...' },
    { progress: 95, step: 'Finalizing report...' },
  ]

  let stepIndex = 0

  const interval = setInterval(() => {
    if (stepIndex < steps.length) {
      const { progress, step } = steps[stepIndex]
      set((state: any) => ({
        tasks: state.tasks.map((t: ResearchTask) =>
          t.id === taskId
            ? { ...t, status: 'running', progress, currentStep: step }
            : t
        ),
        activeTask:
          state.activeTask?.id === taskId
            ? { ...state.activeTask, status: 'running', progress, currentStep: step }
            : state.activeTask,
      }))
      stepIndex++
    } else {
      clearInterval(interval)
      
      // Complete with mock results
      const mockResults: ResearchResult = {
        summary: 'Based on comprehensive analysis, this investment opportunity shows strong fundamentals with moderate risk profile.',
        score: 78,
        recommendation: 'buy',
        sections: [
          {
            title: 'Business Overview',
            content: 'The company operates in a growing market with sustainable competitive advantages.',
            confidence: 0.85,
          },
          {
            title: 'Financial Analysis',
            content: 'Strong revenue growth, improving margins, and healthy balance sheet.',
            confidence: 0.9,
          },
          {
            title: 'Risk Assessment',
            content: 'Key risks include market competition and regulatory changes.',
            confidence: 0.75,
          },
        ],
        sources: [
          { title: 'SEC 10-K Filing', url: '#', type: 'regulatory' },
          { title: 'Earnings Call Transcript', url: '#', type: 'company' },
          { title: 'Industry Report', url: '#', type: 'research' },
        ],
        metrics: {
          pe_ratio: 22.5,
          revenue_growth: 15.3,
          profit_margin: 18.2,
          debt_to_equity: 0.45,
        },
      }

      set((state: any) => ({
        tasks: state.tasks.map((t: ResearchTask) =>
          t.id === taskId
            ? {
                ...t,
                status: 'completed',
                progress: 100,
                currentStep: 'Research complete',
                results: mockResults,
              }
            : t
        ),
        activeTask:
          state.activeTask?.id === taskId
            ? {
                ...state.activeTask,
                status: 'completed',
                progress: 100,
                currentStep: 'Research complete',
                results: mockResults,
              }
            : state.activeTask,
      }))
    }
  }, 2000)
}
