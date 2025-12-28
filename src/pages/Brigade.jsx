import React, { useState, useEffect } from 'react';
import { useToast } from '../components/Toast';

export default function Brigade() {
  const toast = useToast();
  const [selectedAgent, setSelectedAgent] = useState('research');
  const [task, setTask] = useState('');
  const [taskHistory, setTaskHistory] = useState([]);
  const [currentTask, setCurrentTask] = useState(null);
  const [loading, setLoading] = useState(false);
  const [usage, setUsage] = useState(null);
  const [showIframe, setShowIframe] = useState(true);

  useEffect(() => {
    fetchUsage();
    fetchTaskHistory();
  }, []);

  const fetchUsage = async () => {
    try {
      const response = await fetch('/api/v1/brigade/usage');
      const data = await response.json();
      setUsage(data);
    } catch (error) {
      console.error('Error fetching usage:', error);
    }
  };

  const fetchTaskHistory = async () => {
    try {
      const response = await fetch('/api/v1/brigade/tasks/history');
      const data = await response.json();
      setTaskHistory(data.tasks || []);
    } catch (error) {
      console.error('Error fetching history:', error);
    }
  };

  const executeTask = async () => {
    if (!task.trim()) return;

    setLoading(true);
    try {
      const response = await fetch('https://brigade.your-domain.com/api/v1/agents/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          agent_type: selectedAgent,
          task: task
        })
      });

      const result = await response.json();
      setCurrentTask(result);
      setTask('');
      fetchTaskHistory();
      fetchUsage();
    } catch (error) {
      console.error('Error executing task:', error);
      toast.error('Failed to execute task');
    } finally {
      setLoading(false);
    }
  };

  const openFullUI = () => {
    window.open('https://brigade.your-domain.com', '_blank', 'noopener,noreferrer');
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">🦄 Unicorn Brigade</h1>
          <p className="text-gray-500">Multi-agent AI orchestration with persistent memory</p>
        </div>
        <button
          onClick={openFullUI}
          className="bg-purple-600 hover:bg-purple-700 text-white py-2 px-6 rounded-lg transition-colors flex items-center gap-2"
        >
          <span>Open Full UI</span>
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
          </svg>
        </button>
      </div>

      {/* Usage Stats */}
      {usage && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">Usage This Month</h2>
          <div className="grid grid-cols-4 gap-4">
            <div>
              <p className="text-sm text-gray-500">Input Tokens</p>
              <p className="text-2xl font-bold">{usage.input_tokens?.toLocaleString() || 0}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Output Tokens</p>
              <p className="text-2xl font-bold">{usage.output_tokens?.toLocaleString() || 0}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Agent Calls</p>
              <p className="text-2xl font-bold">{usage.agent_calls || 0}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Est. Cost</p>
              <p className="text-2xl font-bold">${usage.estimated_cost?.toFixed(2) || '0.00'}</p>
            </div>
          </div>
        </div>
      )}

      {/* Brigade Dashboard Section */}
      <div className="bg-white rounded-lg shadow overflow-hidden border-2 border-purple-200">
        <div className="bg-gradient-to-r from-purple-50 to-purple-100 p-4 flex items-center justify-between border-b border-purple-200">
          <h2 className="text-xl font-semibold text-purple-900">Brigade Dashboard</h2>
          <button
            onClick={() => setShowIframe(!showIframe)}
            className="bg-white hover:bg-gray-50 text-purple-700 py-2 px-4 rounded-lg transition-colors border border-purple-300 text-sm font-medium"
          >
            {showIframe ? 'Hide Dashboard' : 'Show Dashboard'}
          </button>
        </div>
        {showIframe && (
          <div className="p-0">
            <iframe
              src="https://brigade.your-domain.com"
              title="Unicorn Brigade Dashboard"
              className="w-full border-0"
              style={{
                height: 'calc(100vh - 400px)',
                minHeight: '600px'
              }}
              allow="clipboard-read; clipboard-write"
              sandbox="allow-same-origin allow-scripts allow-forms allow-popups allow-modals"
              aria-label="Brigade AI orchestration dashboard"
            />
          </div>
        )}
      </div>

      {/* Agent Selection & Task Input */}
      <div className="bg-white rounded-lg shadow p-6 space-y-4">
        <h2 className="text-xl font-semibold">Execute Agent Task</h2>
        
        {/* Agent Selection */}
        <div>
          <label className="block text-sm font-medium mb-2">Select Agent</label>
          <div className="grid grid-cols-3 gap-3">
            {[
              { id: 'research', name: 'Research', icon: '🔍', desc: 'Information gathering' },
              { id: 'code', name: 'Code', icon: '💻', desc: 'Code generation' },
              { id: 'analysis', name: 'Analysis', icon: '📊', desc: 'Data analysis' }
            ].map(agent => (
              <button
                key={agent.id}
                onClick={() => setSelectedAgent(agent.id)}
                className={`p-4 border-2 rounded-lg text-left transition ${
                  selectedAgent === agent.id
                    ? 'border-purple-500 bg-purple-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <div className="text-3xl mb-2">{agent.icon}</div>
                <div className="font-medium">{agent.name}</div>
                <div className="text-sm text-gray-500">{agent.desc}</div>
              </button>
            ))}
          </div>
        </div>

        {/* Task Input */}
        <div>
          <label className="block text-sm font-medium mb-2">Task Description</label>
          <textarea
            value={task}
            onChange={(e) => setTask(e.target.value)}
            placeholder="Describe what you want the agent to do..."
            className="w-full p-3 border rounded-lg"
            rows={4}
          />
        </div>

        {/* Execute Button */}
        <button
          onClick={executeTask}
          disabled={loading || !task.trim()}
          className="w-full bg-purple-600 hover:bg-purple-700 text-white py-3 px-6 rounded-lg disabled:opacity-50"
        >
          {loading ? 'Executing...' : 'Execute Task'}
        </button>
      </div>

      {/* Task History */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Recent Tasks</h2>
        <div className="space-y-3">
          {taskHistory.length === 0 ? (
            <p className="text-gray-500 text-center py-8">No tasks yet</p>
          ) : (
            taskHistory.slice(0, 10).map((task, idx) => (
              <div key={idx} className="flex items-center justify-between p-3 border rounded-lg">
                <div className="flex-1">
                  <div className="font-medium">{task.task}</div>
                  <div className="text-sm text-gray-500">
                    {task.agent} • {new Date(task.created_at).toLocaleString()}
                  </div>
                </div>
                <span className={`px-3 py-1 rounded-full text-sm ${
                  task.status === 'completed' ? 'bg-green-100 text-green-800' : 'bg-gray-100'
                }`}>
                  {task.status}
                </span>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
