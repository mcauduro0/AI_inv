// =============================================================================
// Investment Agent System - Frontend Application
// =============================================================================
// React + TypeScript + TailwindCSS frontend for the investment research platform
// =============================================================================

import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

// Layout Components
import { Layout } from './components/Layout';
import { AuthProvider, useAuth } from './contexts/AuthContext';

// Page Components
import { Dashboard } from './pages/Dashboard';
import { ResearchProjects } from './pages/ResearchProjects';
import { ResearchDetail } from './pages/ResearchDetail';
import { IdeaGeneration } from './pages/IdeaGeneration';
import { Screening } from './pages/Screening';
import { Workflows } from './pages/Workflows';
import { Settings } from './pages/Settings';
import { Login } from './pages/Login';

// Create React Query client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      retry: 1,
    },
  },
});

// Protected Route Component
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};

// Main App Component
const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <Router>
          <Routes>
            {/* Public Routes */}
            <Route path="/login" element={<Login />} />

            {/* Protected Routes */}
            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <Layout />
                </ProtectedRoute>
              }
            >
              <Route index element={<Dashboard />} />
              <Route path="research" element={<ResearchProjects />} />
              <Route path="research/:id" element={<ResearchDetail />} />
              <Route path="ideas" element={<IdeaGeneration />} />
              <Route path="screening" element={<Screening />} />
              <Route path="workflows" element={<Workflows />} />
              <Route path="settings" element={<Settings />} />
            </Route>

            {/* Catch all */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Router>
      </AuthProvider>
    </QueryClientProvider>
  );
};

export default App;
