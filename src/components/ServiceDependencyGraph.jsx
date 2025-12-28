import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  XMarkIcon,
  ArrowRightIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon,
  MagnifyingGlassIcon
} from '@heroicons/react/24/outline';

// Service dependency definitions
const SERVICE_DEPENDENCIES = {
  'open-webui': ['postgres', 'redis', 'vllm'],
  'vllm': ['postgres'],
  'searxng': ['redis'],
  'embeddings': ['postgres'],
  'reranker': ['postgres'],
  'whisperx': [],
  'kokoro': [],
  'tika-ocr': [],
  'prometheus': [],
  'gpu-exporter': [],
  'admin-dashboard': ['postgres', 'redis'],
  'qdrant': [],
  'postgres': [],
  'redis': []
};

const SERVICE_CATEGORIES = {
  'Core AI': ['vllm', 'open-webui', 'embeddings', 'reranker'],
  'Speech Processing': ['whisperx', 'kokoro'],
  'Search & Data': ['searxng', 'qdrant', 'postgres', 'redis'],
  'Processing': ['tika-ocr'],
  'Monitoring': ['prometheus', 'gpu-exporter'],
  'Management': ['admin-dashboard']
};

const CATEGORY_COLORS = {
  'Core AI': { bg: 'bg-blue-100 dark:bg-blue-900/20', border: 'border-blue-300 dark:border-blue-600', text: 'text-blue-700 dark:text-blue-300' },
  'Speech Processing': { bg: 'bg-green-100 dark:bg-green-900/20', border: 'border-green-300 dark:border-green-600', text: 'text-green-700 dark:text-green-300' },
  'Search & Data': { bg: 'bg-purple-100 dark:bg-purple-900/20', border: 'border-purple-300 dark:border-purple-600', text: 'text-purple-700 dark:text-purple-300' },
  'Processing': { bg: 'bg-orange-100 dark:bg-orange-900/20', border: 'border-orange-300 dark:border-orange-600', text: 'text-orange-700 dark:text-orange-300' },
  'Monitoring': { bg: 'bg-yellow-100 dark:bg-yellow-900/20', border: 'border-yellow-300 dark:border-yellow-600', text: 'text-yellow-700 dark:text-yellow-300' },
  'Management': { bg: 'bg-gray-100 dark:bg-gray-900/20', border: 'border-gray-300 dark:border-gray-600', text: 'text-gray-700 dark:text-gray-300' }
};

export default function ServiceDependencyGraph({ services, onClose }) {
  const [selectedService, setSelectedService] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [viewMode, setViewMode] = useState('dependencies'); // 'dependencies' or 'dependents'
  const svgRef = useRef(null);

  const getServiceCategory = (serviceName) => {
    for (const [category, serviceList] of Object.entries(SERVICE_CATEGORIES)) {
      if (serviceList.includes(serviceName)) {
        return category;
      }
    }
    return 'Other';
  };

  const getServiceStatus = (serviceName) => {
    const service = services.find(s => s.name === serviceName);
    return service?.status || 'unknown';
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'healthy': return 'fill-green-500';
      case 'starting': return 'fill-blue-500';
      case 'stopped': return 'fill-gray-500';
      case 'error': return 'fill-red-500';
      default: return 'fill-gray-400';
    }
  };

  const getDependents = (serviceName) => {
    return Object.entries(SERVICE_DEPENDENCIES)
      .filter(([_, deps]) => deps.includes(serviceName))
      .map(([service, _]) => service);
  };

  const getFilteredServices = () => {
    const allServices = Object.keys(SERVICE_DEPENDENCIES);
    if (!searchTerm) return allServices;
    
    return allServices.filter(service =>
      service.toLowerCase().includes(searchTerm.toLowerCase()) ||
      getServiceCategory(service).toLowerCase().includes(searchTerm.toLowerCase())
    );
  };

  const renderServiceNode = (serviceName, x, y, isSelected = false, isHighlighted = false) => {
    const status = getServiceStatus(serviceName);
    const category = getServiceCategory(serviceName);
    const categoryColors = CATEGORY_COLORS[category] || CATEGORY_COLORS['Management'];
    
    return (
      <g key={serviceName} transform={`translate(${x}, ${y})`}>
        {/* Node background */}
        <rect
          x="-60"
          y="-30"
          width="120"
          height="60"
          rx="8"
          className={`${categoryColors.bg} ${categoryColors.border} border-2 cursor-pointer transition-all ${
            isSelected ? 'stroke-4 stroke-blue-500' : ''
          } ${
            isHighlighted ? 'opacity-100 scale-110' : searchTerm && !serviceName.toLowerCase().includes(searchTerm.toLowerCase()) ? 'opacity-30' : 'opacity-100'
          }`}
          onClick={() => setSelectedService(selectedService === serviceName ? null : serviceName)}
        />
        
        {/* Status indicator */}
        <circle
          cx="45"
          cy="-20"
          r="6"
          className={getStatusColor(status)}
        />
        
        {/* Service name */}
        <text
          x="0"
          y="-5"
          textAnchor="middle"
          className={`text-sm font-medium ${categoryColors.text} fill-current pointer-events-none`}
        >
          {serviceName}
        </text>
        
        {/* Category */}
        <text
          x="0"
          y="10"
          textAnchor="middle"
          className="text-xs fill-gray-500 pointer-events-none"
        >
          {category}
        </text>
      </g>
    );
  };

  const renderArrow = (fromX, fromY, toX, toY, isHighlighted = false) => {
    const midX = (fromX + toX) / 2;
    const midY = (fromY + toY) / 2;
    const angle = Math.atan2(toY - fromY, toX - fromX);
    
    return (
      <g>
        {/* Arrow line */}
        <line
          x1={fromX}
          y1={fromY}
          x2={toX}
          y2={toY}
          className={`stroke-2 ${
            isHighlighted ? 'stroke-blue-500' : 'stroke-gray-400 dark:stroke-gray-600'
          } transition-all`}
          markerEnd="url(#arrowhead)"
        />
        
        {/* Dependency label */}
        <text
          x={midX}
          y={midY - 5}
          textAnchor="middle"
          className={`text-xs ${
            isHighlighted ? 'fill-blue-600 font-medium' : 'fill-gray-500'
          } pointer-events-none`}
        >
          depends on
        </text>
      </g>
    );
  };

  const calculateNodePositions = () => {
    const filteredServices = getFilteredServices();
    const nodes = {};
    const centerX = 400;
    const centerY = 300;
    const radius = 200;
    
    // Position nodes in a circle
    filteredServices.forEach((service, index) => {
      const angle = (index * 2 * Math.PI) / filteredServices.length;
      nodes[service] = {
        x: centerX + radius * Math.cos(angle),
        y: centerY + radius * Math.sin(angle)
      };
    });

    // If a service is selected, position its dependencies/dependents in inner circle
    if (selectedService) {
      const relatedServices = viewMode === 'dependencies' 
        ? SERVICE_DEPENDENCIES[selectedService] || []
        : getDependents(selectedService);
      
      relatedServices.forEach((service, index) => {
        if (nodes[service]) {
          const angle = (index * 2 * Math.PI) / relatedServices.length;
          nodes[service] = {
            x: centerX + (radius * 0.6) * Math.cos(angle),
            y: centerY + (radius * 0.6) * Math.sin(angle)
          };
        }
      });

      // Center the selected service
      nodes[selectedService] = { x: centerX, y: centerY };
    }

    return nodes;
  };

  const nodePositions = calculateNodePositions();
  const filteredServices = getFilteredServices();

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
        onClick={onClose}
      >
        <motion.div
          initial={{ scale: 0.95, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.95, opacity: 0 }}
          className="bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-6xl h-5/6 flex flex-col overflow-hidden"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b dark:border-gray-700">
            <div>
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
                Service Dependencies
              </h2>
              <p className="text-gray-600 dark:text-gray-400 mt-1">
                Visualize service relationships and dependencies
              </p>
            </div>
            
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
            >
              <XMarkIcon className="h-6 w-6 text-gray-400" />
            </button>
          </div>

          {/* Controls */}
          <div className="flex items-center gap-4 p-4 border-b dark:border-gray-700 bg-gray-50 dark:bg-gray-900/50">
            {/* Search */}
            <div className="flex-1 relative">
              <MagnifyingGlassIcon className="h-5 w-5 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
              <input
                type="text"
                placeholder="Search services..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
              />
            </div>

            {/* View Mode */}
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-600 dark:text-gray-400">View:</span>
              <select
                value={viewMode}
                onChange={(e) => setViewMode(e.target.value)}
                className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
              >
                <option value="dependencies">Dependencies</option>
                <option value="dependents">Dependents</option>
              </select>
            </div>

            {/* Clear Selection */}
            {selectedService && (
              <button
                onClick={() => setSelectedService(null)}
                className="px-3 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
              >
                Clear Selection
              </button>
            )}
          </div>

          {/* Graph */}
          <div className="flex-1 overflow-auto p-4">
            <svg
              ref={svgRef}
              width="800"
              height="600"
              viewBox="0 0 800 600"
              className="w-full h-full"
            >
              {/* Arrow marker definition */}
              <defs>
                <marker
                  id="arrowhead"
                  markerWidth="10"
                  markerHeight="7"
                  refX="9"
                  refY="3.5"
                  orient="auto"
                >
                  <polygon
                    points="0 0, 10 3.5, 0 7"
                    className="fill-gray-400 dark:fill-gray-600"
                  />
                </marker>
              </defs>

              {/* Render dependency arrows */}
              {selectedService && filteredServices.includes(selectedService) && (
                <>
                  {viewMode === 'dependencies' && (
                    <>
                      {(SERVICE_DEPENDENCIES[selectedService] || []).map(dependency => {
                        if (!filteredServices.includes(dependency)) return null;
                        
                        const fromPos = nodePositions[selectedService];
                        const toPos = nodePositions[dependency];
                        
                        if (fromPos && toPos) {
                          return renderArrow(fromPos.x, fromPos.y, toPos.x, toPos.y, true);
                        }
                        return null;
                      })}
                    </>
                  )}
                  
                  {viewMode === 'dependents' && (
                    <>
                      {getDependents(selectedService).map(dependent => {
                        if (!filteredServices.includes(dependent)) return null;
                        
                        const fromPos = nodePositions[dependent];
                        const toPos = nodePositions[selectedService];
                        
                        if (fromPos && toPos) {
                          return renderArrow(fromPos.x, fromPos.y, toPos.x, toPos.y, true);
                        }
                        return null;
                      })}
                    </>
                  )}
                </>
              )}

              {/* Render service nodes */}
              {filteredServices.map(service => {
                const position = nodePositions[service];
                if (!position) return null;
                
                const isSelected = selectedService === service;
                const isHighlighted = selectedService && (
                  (viewMode === 'dependencies' && SERVICE_DEPENDENCIES[selectedService]?.includes(service)) ||
                  (viewMode === 'dependents' && getDependents(selectedService).includes(service))
                );

                return renderServiceNode(service, position.x, position.y, isSelected, isHighlighted);
              })}
            </svg>
          </div>

          {/* Info Panel */}
          <div className="border-t dark:border-gray-700 p-4 bg-gray-50 dark:bg-gray-900/50">
            {selectedService ? (
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <InformationCircleIcon className="h-5 w-5 text-blue-600" />
                  <h3 className="font-semibold text-gray-900 dark:text-white">
                    {selectedService}
                  </h3>
                  <span className={`px-2 py-1 text-xs rounded-full ${
                    getServiceStatus(selectedService) === 'healthy' ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' :
                    getServiceStatus(selectedService) === 'stopped' ? 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200' :
                    'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                  }`}>
                    {getServiceStatus(selectedService)}
                  </span>
                </div>
                
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="font-medium text-gray-700 dark:text-gray-300">Dependencies:</span>
                    <div className="mt-1">
                      {SERVICE_DEPENDENCIES[selectedService]?.length > 0 ? (
                        <div className="flex flex-wrap gap-1">
                          {SERVICE_DEPENDENCIES[selectedService].map(dep => (
                            <span key={dep} className="px-2 py-1 bg-blue-100 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300 rounded text-xs">
                              {dep}
                            </span>
                          ))}
                        </div>
                      ) : (
                        <span className="text-gray-500 dark:text-gray-400">None</span>
                      )}
                    </div>
                  </div>
                  
                  <div>
                    <span className="font-medium text-gray-700 dark:text-gray-300">Dependents:</span>
                    <div className="mt-1">
                      {getDependents(selectedService).length > 0 ? (
                        <div className="flex flex-wrap gap-1">
                          {getDependents(selectedService).map(dep => (
                            <span key={dep} className="px-2 py-1 bg-green-100 dark:bg-green-900/20 text-green-700 dark:text-green-300 rounded text-xs">
                              {dep}
                            </span>
                          ))}
                        </div>
                      ) : (
                        <span className="text-gray-500 dark:text-gray-400">None</span>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-center text-gray-500 dark:text-gray-400">
                <InformationCircleIcon className="h-8 w-8 mx-auto mb-2 opacity-50" />
                <p>Click on any service to view its dependencies and relationships</p>
              </div>
            )}
          </div>

          {/* Legend */}
          <div className="border-t dark:border-gray-700 p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4 text-sm">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                  <span className="text-gray-600 dark:text-gray-400">Healthy</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
                  <span className="text-gray-600 dark:text-gray-400">Starting</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 bg-gray-500 rounded-full"></div>
                  <span className="text-gray-600 dark:text-gray-400">Stopped</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 bg-red-500 rounded-full"></div>
                  <span className="text-gray-600 dark:text-gray-400">Error</span>
                </div>
              </div>
              
              <div className="text-sm text-gray-600 dark:text-gray-400">
                {filteredServices.length} services shown
              </div>
            </div>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}