// =============================================================================
// Dashboard Page
// =============================================================================
// Main dashboard showing research overview, recent activity, and quick actions
// =============================================================================

import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import {
  ChartBarIcon,
  DocumentTextIcon,
  LightBulbIcon,
  PlayIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  ClockIcon,
} from '@heroicons/react/24/outline';

import { api } from '../services/api';

// Types
interface ResearchProject {
  id: string;
  name: string;
  ticker: string;
  status: string;
  conviction_level: string | null;
  updated_at: string;
}

interface WorkflowRun {
  id: string;
  workflow_name: string;
  status: string;
  started_at: string;
}

interface DashboardStats {
  active_research: number;
  ideas_generated: number;
  workflows_run: number;
  tasks_completed: number;
}

// Stat Card Component
const StatCard: React.FC<{
  title: string;
  value: number | string;
  icon: React.ElementType;
  trend?: number;
  color: string;
}> = ({ title, value, icon: Icon, trend, color }) => (
  <div className="bg-white rounded-lg shadow p-6">
    <div className="flex items-center justify-between">
      <div>
        <p className="text-sm font-medium text-gray-500">{title}</p>
        <p className="text-3xl font-bold text-gray-900 mt-1">{value}</p>
        {trend !== undefined && (
          <div className="flex items-center mt-2">
            {trend >= 0 ? (
              <ArrowTrendingUpIcon className="h-4 w-4 text-green-500" />
            ) : (
              <ArrowTrendingDownIcon className="h-4 w-4 text-red-500" />
            )}
            <span
              className={`text-sm ml-1 ${
                trend >= 0 ? 'text-green-500' : 'text-red-500'
              }`}
            >
              {Math.abs(trend)}% from last week
            </span>
          </div>
        )}
      </div>
      <div className={`p-3 rounded-full ${color}`}>
        <Icon className="h-6 w-6 text-white" />
      </div>
    </div>
  </div>
);

// Quick Action Button
const QuickAction: React.FC<{
  title: string;
  description: string;
  icon: React.ElementType;
  to: string;
  color: string;
}> = ({ title, description, icon: Icon, to, color }) => (
  <Link
    to={to}
    className="block bg-white rounded-lg shadow p-6 hover:shadow-lg transition-shadow"
  >
    <div className="flex items-start">
      <div className={`p-3 rounded-lg ${color}`}>
        <Icon className="h-6 w-6 text-white" />
      </div>
      <div className="ml-4">
        <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
        <p className="text-sm text-gray-500 mt-1">{description}</p>
      </div>
    </div>
  </Link>
);

// Research Project Card
const ResearchCard: React.FC<{ project: ResearchProject }> = ({ project }) => {
  const statusColors: Record<string, string> = {
    idea: 'bg-gray-100 text-gray-800',
    screening: 'bg-yellow-100 text-yellow-800',
    deep_dive: 'bg-blue-100 text-blue-800',
    thesis_development: 'bg-purple-100 text-purple-800',
    monitoring: 'bg-green-100 text-green-800',
  };

  const convictionColors: Record<string, string> = {
    low: 'text-gray-500',
    medium: 'text-yellow-500',
    high: 'text-green-500',
    very_high: 'text-green-700',
  };

  return (
    <Link
      to={`/research/${project.id}`}
      className="block bg-white rounded-lg shadow p-4 hover:shadow-md transition-shadow"
    >
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center">
            <span className="text-lg font-bold text-gray-900">
              {project.ticker}
            </span>
            <span
              className={`ml-2 px-2 py-1 rounded-full text-xs font-medium ${
                statusColors[project.status] || 'bg-gray-100 text-gray-800'
              }`}
            >
              {project.status.replace('_', ' ')}
            </span>
          </div>
          <p className="text-sm text-gray-500 mt-1">{project.name}</p>
        </div>
        {project.conviction_level && (
          <div className="text-right">
            <p className="text-xs text-gray-500">Conviction</p>
            <p
              className={`font-semibold ${
                convictionColors[project.conviction_level] || 'text-gray-500'
              }`}
            >
              {project.conviction_level.replace('_', ' ').toUpperCase()}
            </p>
          </div>
        )}
      </div>
      <div className="mt-3 flex items-center text-xs text-gray-400">
        <ClockIcon className="h-4 w-4 mr-1" />
        Updated {new Date(project.updated_at).toLocaleDateString()}
      </div>
    </Link>
  );
};

// Main Dashboard Component
export const Dashboard: React.FC = () => {
  // Fetch dashboard stats
  const { data: stats } = useQuery<DashboardStats>({
    queryKey: ['dashboard-stats'],
    queryFn: () => api.get('/dashboard/stats').then((res) => res.data),
  });

  // Fetch recent research projects
  const { data: recentProjects } = useQuery<ResearchProject[]>({
    queryKey: ['recent-projects'],
    queryFn: () =>
      api.get('/research?limit=5&sort=-updated_at').then((res) => res.data),
  });

  // Fetch recent workflow runs
  const { data: recentWorkflows } = useQuery<WorkflowRun[]>({
    queryKey: ['recent-workflows'],
    queryFn: () =>
      api.get('/workflows/runs?limit=5&sort=-started_at').then((res) => res.data),
  });

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-500 mt-1">
          Overview of your investment research activity
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Active Research"
          value={stats?.active_research || 0}
          icon={DocumentTextIcon}
          trend={12}
          color="bg-blue-500"
        />
        <StatCard
          title="Ideas Generated"
          value={stats?.ideas_generated || 0}
          icon={LightBulbIcon}
          trend={8}
          color="bg-yellow-500"
        />
        <StatCard
          title="Workflows Run"
          value={stats?.workflows_run || 0}
          icon={PlayIcon}
          trend={-5}
          color="bg-purple-500"
        />
        <StatCard
          title="Tasks Completed"
          value={stats?.tasks_completed || 0}
          icon={ChartBarIcon}
          trend={15}
          color="bg-green-500"
        />
      </div>

      {/* Quick Actions */}
      <div>
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          Quick Actions
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <QuickAction
            title="Start Research"
            description="Begin a new company research project"
            icon={DocumentTextIcon}
            to="/research?action=new"
            color="bg-blue-500"
          />
          <QuickAction
            title="Generate Ideas"
            description="Find new investment opportunities"
            icon={LightBulbIcon}
            to="/ideas"
            color="bg-yellow-500"
          />
          <QuickAction
            title="Run Screening"
            description="Screen stocks based on criteria"
            icon={ChartBarIcon}
            to="/screening"
            color="bg-green-500"
          />
        </div>
      </div>

      {/* Two Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Recent Research */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">
              Recent Research
            </h2>
            <Link
              to="/research"
              className="text-sm text-blue-600 hover:text-blue-800"
            >
              View all →
            </Link>
          </div>
          <div className="space-y-4">
            {recentProjects?.map((project) => (
              <ResearchCard key={project.id} project={project} />
            ))}
            {(!recentProjects || recentProjects.length === 0) && (
              <div className="text-center py-8 bg-gray-50 rounded-lg">
                <DocumentTextIcon className="h-12 w-12 text-gray-400 mx-auto" />
                <p className="text-gray-500 mt-2">No research projects yet</p>
                <Link
                  to="/research?action=new"
                  className="text-blue-600 hover:text-blue-800 text-sm mt-1 inline-block"
                >
                  Start your first research →
                </Link>
              </div>
            )}
          </div>
        </div>

        {/* Recent Workflows */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">
              Recent Workflows
            </h2>
            <Link
              to="/workflows"
              className="text-sm text-blue-600 hover:text-blue-800"
            >
              View all →
            </Link>
          </div>
          <div className="bg-white rounded-lg shadow">
            <ul className="divide-y divide-gray-200">
              {recentWorkflows?.map((workflow) => (
                <li key={workflow.id} className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium text-gray-900">
                        {workflow.workflow_name}
                      </p>
                      <p className="text-sm text-gray-500">
                        {new Date(workflow.started_at).toLocaleString()}
                      </p>
                    </div>
                    <span
                      className={`px-2 py-1 rounded-full text-xs font-medium ${
                        workflow.status === 'completed'
                          ? 'bg-green-100 text-green-800'
                          : workflow.status === 'running'
                          ? 'bg-blue-100 text-blue-800'
                          : workflow.status === 'failed'
                          ? 'bg-red-100 text-red-800'
                          : 'bg-gray-100 text-gray-800'
                      }`}
                    >
                      {workflow.status}
                    </span>
                  </div>
                </li>
              ))}
              {(!recentWorkflows || recentWorkflows.length === 0) && (
                <li className="p-8 text-center">
                  <PlayIcon className="h-12 w-12 text-gray-400 mx-auto" />
                  <p className="text-gray-500 mt-2">No workflow runs yet</p>
                </li>
              )}
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};
