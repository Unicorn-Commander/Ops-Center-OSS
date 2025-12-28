import React, { useState } from 'react';
import { XMarkIcon, BookOpenIcon, AcademicCapIcon, QuestionMarkCircleIcon } from '@heroicons/react/24/outline';

const helpContent = {
  dashboard: {
    title: 'Dashboard Help',
    sections: [
      {
        title: 'Quick Stats',
        content: 'The four cards at the top show real-time system metrics: Active Services, GPU Usage, Memory Usage, and Connection Status.'
      },
      {
        title: 'System Status',
        content: 'Detailed GPU and system resource monitoring. Keep GPU usage below 90% for optimal performance.'
      },
      {
        title: 'Extensions',
        content: 'Start and stop optional services like Ollama, ComfyUI, and monitoring tools. Green dots indicate running services.'
      }
    ]
  },
  models: {
    title: 'Model Management Help',
    sections: [
      {
        title: 'Searching Models',
        content: 'Type to search Hugging Face models in real-time. Results show vLLM-compatible models with quantization options.'
      },
      {
        title: 'Memory Estimation',
        content: 'Select a quantization to see memory requirements. The estimation includes model size, context memory, and overhead.'
      },
      {
        title: 'Model Retention',
        content: 'Set how long models stay loaded in GPU memory. "Keep Forever" prevents automatic unloading.'
      },
      {
        title: 'Context Size',
        content: 'Higher context allows longer conversations but uses more memory. Default is 16,384 tokens.'
      }
    ]
  },
  services: {
    title: 'Services Help',
    sections: [
      {
        title: 'Service Status',
        content: 'Green = Healthy, Yellow = Starting, Red = Unhealthy. Click a service card to open its web interface.'
      },
      {
        title: 'Service Actions',
        content: 'Hover over a service to see Restart and View Logs buttons. Use with caution during active operations.'
      }
    ]
  },
  network: {
    title: 'Network Help',
    sections: [
      {
        title: 'WiFi Connection',
        content: 'Click "Scan Networks" to find available WiFi. Click a network and enter password to connect.'
      },
      {
        title: 'Network Configuration',
        content: 'Click "Configure" to set static IP or DHCP. Changes apply immediately - ensure settings are correct.'
      }
    ]
  },
  settings: {
    title: 'Settings Help',
    sections: [
      {
        title: 'System Settings',
        content: 'Configure model idle timeout and memory limits. These affect all services globally.'
      },
      {
        title: 'Notifications',
        content: 'Set up email or webhook alerts for system events and errors.'
      },
      {
        title: 'Backup',
        content: 'Automated backups run daily at 2 AM by default. Adjust schedule using cron syntax.'
      }
    ]
  }
};

export default function HelpPanel({ isOpen, onClose, currentPage = 'dashboard' }) {
  const [activeTab, setActiveTab] = useState('help');
  
  if (!isOpen) return null;
  
  const pageHelp = helpContent[currentPage] || helpContent.dashboard;

  return (
    <div className="fixed inset-y-0 right-0 w-96 bg-white dark:bg-gray-800 shadow-2xl z-50 flex flex-col">
      {/* Header */}
      <div className="p-4 border-b dark:border-gray-700">
        <div className="flex justify-between items-center">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            Help & Documentation
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 dark:text-gray-500 dark:hover:text-gray-300"
          >
            <XMarkIcon className="h-5 w-5" />
          </button>
        </div>
        
        {/* Tabs */}
        <div className="flex gap-4 mt-4">
          <button
            onClick={() => setActiveTab('help')}
            className={`flex items-center gap-2 px-3 py-1 rounded ${
              activeTab === 'help' 
                ? 'bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300' 
                : 'text-gray-600 dark:text-gray-400'
            }`}
          >
            <QuestionMarkCircleIcon className="h-4 w-4" />
            Help
          </button>
          <button
            onClick={() => setActiveTab('tutorial')}
            className={`flex items-center gap-2 px-3 py-1 rounded ${
              activeTab === 'tutorial' 
                ? 'bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300' 
                : 'text-gray-600 dark:text-gray-400'
            }`}
          >
            <AcademicCapIcon className="h-4 w-4" />
            Tutorial
          </button>
          <button
            onClick={() => setActiveTab('docs')}
            className={`flex items-center gap-2 px-3 py-1 rounded ${
              activeTab === 'docs' 
                ? 'bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300' 
                : 'text-gray-600 dark:text-gray-400'
            }`}
          >
            <BookOpenIcon className="h-4 w-4" />
            Docs
          </button>
        </div>
      </div>
      
      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4">
        {activeTab === 'help' && (
          <div className="space-y-6">
            <h3 className="text-lg font-medium text-gray-900 dark:text-white">
              {pageHelp.title}
            </h3>
            {pageHelp.sections.map((section, index) => (
              <div key={index}>
                <h4 className="font-medium text-gray-800 dark:text-gray-200 mb-2">
                  {section.title}
                </h4>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  {section.content}
                </p>
              </div>
            ))}
          </div>
        )}
        
        {activeTab === 'tutorial' && (
          <div className="space-y-4">
            <h3 className="text-lg font-medium text-gray-900 dark:text-white">
              Quick Start Tutorial
            </h3>
            <ol className="space-y-3 text-sm">
              <li className="flex gap-3">
                <span className="flex-shrink-0 w-6 h-6 bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 rounded-full flex items-center justify-center text-xs font-medium">
                  1
                </span>
                <div>
                  <p className="font-medium text-gray-800 dark:text-gray-200">Check System Status</p>
                  <p className="text-gray-600 dark:text-gray-400">Ensure GPU and services are running properly on the dashboard.</p>
                </div>
              </li>
              <li className="flex gap-3">
                <span className="flex-shrink-0 w-6 h-6 bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 rounded-full flex items-center justify-center text-xs font-medium">
                  2
                </span>
                <div>
                  <p className="font-medium text-gray-800 dark:text-gray-200">Browse and Download Models</p>
                  <p className="text-gray-600 dark:text-gray-400">Go to Models page, search for models, and download with appropriate quantization.</p>
                </div>
              </li>
              <li className="flex gap-3">
                <span className="flex-shrink-0 w-6 h-6 bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 rounded-full flex items-center justify-center text-xs font-medium">
                  3
                </span>
                <div>
                  <p className="font-medium text-gray-800 dark:text-gray-200">Start Using AI Services</p>
                  <p className="text-gray-600 dark:text-gray-400">Open Chat Interface (Open-WebUI) to start chatting with your AI models.</p>
                </div>
              </li>
              <li className="flex gap-3">
                <span className="flex-shrink-0 w-6 h-6 bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 rounded-full flex items-center justify-center text-xs font-medium">
                  4
                </span>
                <div>
                  <p className="font-medium text-gray-800 dark:text-gray-200">Enable Extensions</p>
                  <p className="text-gray-600 dark:text-gray-400">Start Ollama for additional model support or Monitoring for Grafana dashboards.</p>
                </div>
              </li>
            </ol>
          </div>
        )}
        
        {activeTab === 'docs' && (
          <div className="space-y-4">
            <h3 className="text-lg font-medium text-gray-900 dark:text-white">
              Documentation Links
            </h3>
            <div className="space-y-2">
              <a 
                href="http://localhost:8081" 
                target="_blank" 
                rel="noopener noreferrer"
                className="block p-3 bg-gray-100 dark:bg-gray-700 rounded hover:bg-gray-200 dark:hover:bg-gray-600"
              >
                <p className="font-medium text-gray-800 dark:text-gray-200">📚 Full Documentation</p>
                <p className="text-sm text-gray-600 dark:text-gray-400">Complete UC-1 Pro documentation</p>
              </a>
              <a 
                href="https://github.com/Unicorn-Commander/UC-1-Pro" 
                target="_blank" 
                rel="noopener noreferrer"
                className="block p-3 bg-gray-100 dark:bg-gray-700 rounded hover:bg-gray-200 dark:hover:bg-gray-600"
              >
                <p className="font-medium text-gray-800 dark:text-gray-200">🐙 GitHub Repository</p>
                <p className="text-sm text-gray-600 dark:text-gray-400">Source code and issues</p>
              </a>
              <a 
                href="https://ollama.ai/library" 
                target="_blank" 
                rel="noopener noreferrer"
                className="block p-3 bg-gray-100 dark:bg-gray-700 rounded hover:bg-gray-200 dark:hover:bg-gray-600"
              >
                <p className="font-medium text-gray-800 dark:text-gray-200">🦙 Ollama Models</p>
                <p className="text-sm text-gray-600 dark:text-gray-400">Browse Ollama model library</p>
              </a>
            </div>
          </div>
        )}
      </div>
      
      {/* Footer */}
      <div className="p-4 border-t dark:border-gray-700 text-center text-sm text-gray-500 dark:text-gray-400">
        Press <kbd className="px-2 py-1 bg-gray-200 dark:bg-gray-700 rounded">?</kbd> for keyboard shortcuts
      </div>
    </div>
  );
}