// =============================================================================
// API Service
// =============================================================================
// Axios-based API client for communicating with the backend services
// =============================================================================

import axios, { AxiosError, AxiosInstance, AxiosRequestConfig } from 'axios';

// Configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';
const AUTH_TOKEN_KEY = 'auth_token';
const REFRESH_TOKEN_KEY = 'refresh_token';

// Create axios instance
export const api: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem(AUTH_TOKEN_KEY);
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for token refresh
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as AxiosRequestConfig & { _retry?: boolean };

    // If 401 and not already retrying, attempt token refresh
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY);
        if (refreshToken) {
          const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
            refresh_token: refreshToken,
          });

          const { access_token, refresh_token } = response.data;
          localStorage.setItem(AUTH_TOKEN_KEY, access_token);
          localStorage.setItem(REFRESH_TOKEN_KEY, refresh_token);

          // Retry original request with new token
          if (originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${access_token}`;
          }
          return api(originalRequest);
        }
      } catch (refreshError) {
        // Refresh failed, clear tokens and redirect to login
        localStorage.removeItem(AUTH_TOKEN_KEY);
        localStorage.removeItem(REFRESH_TOKEN_KEY);
        window.location.href = '/login';
      }
    }

    return Promise.reject(error);
  }
);

// =============================================================================
// Auth API
// =============================================================================

export const authApi = {
  login: async (email: string, password: string) => {
    const formData = new FormData();
    formData.append('username', email);
    formData.append('password', password);

    const response = await api.post('/auth/token', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });

    const { access_token, refresh_token } = response.data;
    localStorage.setItem(AUTH_TOKEN_KEY, access_token);
    localStorage.setItem(REFRESH_TOKEN_KEY, refresh_token);

    return response.data;
  },

  logout: () => {
    localStorage.removeItem(AUTH_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
  },

  register: async (email: string, password: string, fullName?: string) => {
    return api.post('/auth/register', { email, password, full_name: fullName });
  },

  getCurrentUser: () => api.get('/auth/me'),

  isAuthenticated: () => !!localStorage.getItem(AUTH_TOKEN_KEY),
};

// =============================================================================
// Research API
// =============================================================================

export const researchApi = {
  // Projects
  getProjects: (params?: {
    status?: string;
    skip?: number;
    limit?: number;
  }) => api.get('/research', { params }),

  getProject: (id: string) => api.get(`/research/${id}`),

  createProject: (data: {
    ticker: string;
    name?: string;
    research_type?: string;
  }) => api.post('/research/start', data),

  updateProject: (id: string, data: Partial<{
    name: string;
    status: string;
    thesis_summary: string;
    bull_case: string;
    bear_case: string;
    target_price: number;
    conviction_level: string;
  }>) => api.put(`/research/${id}`, data),

  deleteProject: (id: string) => api.delete(`/research/${id}`),

  // Notes
  getProjectNotes: (projectId: string) =>
    api.get(`/research/${projectId}/notes`),

  addNote: (projectId: string, data: {
    title: string;
    content: string;
    note_type?: string;
  }) => api.post(`/research/${projectId}/notes`, data),
};

// =============================================================================
// Idea Generation API
// =============================================================================

export const ideaApi = {
  generateThematic: (data: {
    theme: string;
    sector?: string;
    strategy?: string;
  }) => api.post('/ideas/generate', { ...data, strategy: 'thematic' }),

  generateContrarian: () =>
    api.post('/ideas/generate', { strategy: 'contrarian' }),

  generateFromSources: (sources: string[]) =>
    api.post('/ideas/generate', { sources }),

  getRecentIdeas: (limit?: number) =>
    api.get('/ideas/recent', { params: { limit } }),
};

// =============================================================================
// Screening API
// =============================================================================

export const screeningApi = {
  runScreen: (data: {
    screener_name: string;
    criteria: Record<string, { min?: number; max?: number }>;
    universe?: string;
    limit?: number;
  }) => api.post('/screening/run', data),

  getScreeners: () => api.get('/screening/screeners'),

  getScreenerResults: (screenerName: string, limit?: number) =>
    api.get(`/screening/results/${screenerName}`, { params: { limit } }),
};

// =============================================================================
// Workflow API
// =============================================================================

export const workflowApi = {
  getWorkflows: (params?: {
    workflow_type?: string;
    status?: string;
    skip?: number;
    limit?: number;
  }) => api.get('/workflows', { params }),

  getWorkflow: (id: string) => api.get(`/workflows/${id}`),

  createWorkflow: (data: {
    name: string;
    workflow_type: string;
    description?: string;
    config?: Record<string, unknown>;
    schedule?: string;
  }) => api.post('/workflows', data),

  runWorkflow: (id: string, inputData?: Record<string, unknown>) =>
    api.post(`/workflows/${id}/run`, { input_data: inputData }),

  getWorkflowRuns: (workflowId: string, limit?: number) =>
    api.get(`/workflows/${workflowId}/runs`, { params: { limit } }),

  getRunStatus: (runId: string) => api.get(`/workflows/runs/${runId}`),
};

// =============================================================================
// Task API
// =============================================================================

export const taskApi = {
  createTask: (data: {
    agent_type: string;
    prompt_name: string;
    input_data: Record<string, unknown>;
    priority?: string;
  }) => api.post('/tasks', data),

  getTask: (taskId: string) => api.get(`/tasks/${taskId}`),

  getTasks: (params?: {
    agent_type?: string;
    status?: string;
    skip?: number;
    limit?: number;
  }) => api.get('/tasks', { params }),

  getAgents: () => api.get('/agents'),
};

// =============================================================================
// Dashboard API
// =============================================================================

export const dashboardApi = {
  getStats: () => api.get('/dashboard/stats'),

  getRecentActivity: (limit?: number) =>
    api.get('/dashboard/activity', { params: { limit } }),

  getMetrics: (days?: number) =>
    api.get('/metrics/tasks', { params: { days } }),
};

export default api;
