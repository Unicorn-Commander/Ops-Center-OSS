import React from 'react';
import {
  ServerIcon,
  CpuChipIcon,
  CheckCircleIcon,
  DocumentTextIcon,
  ArrowTopRightOnSquareIcon,
  QuestionMarkCircleIcon
} from '@heroicons/react/24/outline';
import { serviceInfo, modelTips } from '../../data/serviceInfo';

export default function ServiceInfoCard({ activeTab }) {
  const service = serviceInfo[activeTab];
  const tips = modelTips[activeTab];

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
      <div className="flex justify-between items-start">
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-3">
            {activeTab === 'vllm' || activeTab === 'ollama' ? (
              <ServerIcon className="h-8 w-8 text-blue-500" />
            ) : (
              <CpuChipIcon className="h-8 w-8 text-purple-500" />
            )}
            <div>
              <h3 className="text-xl font-semibold text-gray-900 dark:text-white">
                {service.name}
              </h3>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {activeTab === 'vllm' || activeTab === 'ollama' ? 'GPU Accelerated' : 'Intel iGPU Optimized'}
              </p>
            </div>
          </div>

          <p className="text-gray-600 dark:text-gray-300 mb-4">
            {service.description}
          </p>

          <div className="grid grid-cols-2 gap-4 mb-4">
            <div>
              <h4 className="font-medium text-gray-900 dark:text-white mb-2">Key Features:</h4>
              <ul className="text-sm text-gray-600 dark:text-gray-400 space-y-1">
                {service?.features?.slice(0, 3).map((feature, idx) => (
                  <li key={idx} className="flex items-start">
                    <CheckCircleIcon className="h-4 w-4 text-green-500 mr-2 mt-0.5 flex-shrink-0" />
                    {feature}
                  </li>
                ))}
              </ul>
            </div>

            <div>
              <h4 className="font-medium text-gray-900 dark:text-white mb-2">Compatible Models:</h4>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                {service?.compatibleModels}
              </p>

              <div className="mt-3 bg-blue-50 dark:bg-blue-900/20 rounded p-2">
                <p className="text-xs text-blue-800 dark:text-blue-200">
                  <strong>Tip:</strong> {tips?.selection}
                </p>
              </div>
            </div>
          </div>

          <div className="flex gap-3">
            {service?.homepage && (
              <a
                href={service.homepage}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 text-sm text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
              >
                <ArrowTopRightOnSquareIcon className="h-4 w-4" />
                Homepage
              </a>
            )}
            {service?.github && (
              <a
                href={service.github}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 text-sm text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
              >
                <ArrowTopRightOnSquareIcon className="h-4 w-4" />
                GitHub
              </a>
            )}
            {service?.docs && (
              <a
                href={service.docs}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 text-sm text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
              >
                <DocumentTextIcon className="h-4 w-4" />
                Documentation
              </a>
            )}
          </div>
        </div>

        <div className="ml-4">
          <div className="relative group">
            <QuestionMarkCircleIcon className="h-6 w-6 text-gray-400 hover:text-gray-600 cursor-help" />
            <div className="absolute right-0 mt-2 w-64 p-3 bg-gray-900 text-white text-xs rounded-lg shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-10">
              <div className="space-y-2">
                <p><strong>Memory:</strong> {tips?.memory}</p>
                <p><strong>Performance:</strong> {tips?.performance}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
