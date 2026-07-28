import React from 'react';
import { motion } from 'framer-motion';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg p-3">
        <p className="text-gray-900 dark:text-white font-medium mb-2">{`Time: ${label}`}</p>
        {payload.map((entry, index) => (
          <p key={index} className="text-sm" style={{ color: entry.color }}>
            {`${entry.name}: ${entry.value.toFixed(1)}%`}
          </p>
        ))}
      </div>
    );
  }
  return null;
};

export default function PerformanceChart({ data }) {
  if (!data || data.length === 0) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Real-time Performance
        </h2>
        <div className="flex items-center justify-center h-64 text-gray-500 dark:text-gray-400">
          <div className="text-center">
            <div className="animate-pulse mb-2">📊</div>
            <p>Collecting performance data...</p>
          </div>
        </div>
      </div>
    );
  }
  
  return (
    <motion.div
      className="bg-white dark:bg-gray-800 rounded-lg shadow p-6"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
          Real-time Performance
        </h2>
        
        <div className="flex items-center gap-4 text-sm">
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
            <span className="text-gray-600 dark:text-gray-400">CPU</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 bg-green-500 rounded-full"></div>
            <span className="text-gray-600 dark:text-gray-400">Memory</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 bg-purple-500 rounded-full"></div>
            <span className="text-gray-600 dark:text-gray-400">GPU</span>
          </div>
        </div>
      </div>
      
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid 
              strokeDasharray="3 3" 
              stroke="#374151" 
              opacity={0.3}
            />
            <XAxis 
              dataKey="time" 
              axisLine={false}
              tickLine={false}
              tick={{ fill: '#6B7280', fontSize: 12 }}
              interval="preserveStartEnd"
            />
            <YAxis 
              domain={[0, 100]}
              axisLine={false}
              tickLine={false}
              tick={{ fill: '#6B7280', fontSize: 12 }}
              label={{ 
                value: 'Usage (%)', 
                angle: -90, 
                position: 'insideLeft',
                style: { textAnchor: 'middle', fill: '#6B7280' }
              }}
            />
            <Tooltip content={<CustomTooltip />} />
            
            <Line
              type="monotone"
              dataKey="cpu"
              stroke="#3B82F6"
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4, fill: '#3B82F6' }}
              name="CPU"
            />
            
            <Line
              type="monotone"
              dataKey="memory"
              stroke="#10B981"
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4, fill: '#10B981' }}
              name="Memory"
            />
            
            <Line
              type="monotone"
              dataKey="gpu"
              stroke="#8B5CF6"
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4, fill: '#8B5CF6' }}
              name="GPU"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
      
      {/* Current Values */}
      <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
        <div className="grid grid-cols-3 gap-4 text-sm">
          <div className="text-center">
            <div className="text-blue-600 dark:text-blue-400 font-semibold text-lg">
              {data[data.length - 1]?.cpu?.toFixed(1) || 0}%
            </div>
            <div className="text-gray-600 dark:text-gray-400">CPU Usage</div>
          </div>
          
          <div className="text-center">
            <div className="text-green-600 dark:text-green-400 font-semibold text-lg">
              {data[data.length - 1]?.memory?.toFixed(1) || 0}%
            </div>
            <div className="text-gray-600 dark:text-gray-400">Memory Usage</div>
          </div>
          
          <div className="text-center">
            <div className="text-purple-600 dark:text-purple-400 font-semibold text-lg">
              {data[data.length - 1]?.gpu?.toFixed(1) || 0}%
            </div>
            <div className="text-gray-600 dark:text-gray-400">GPU Usage</div>
          </div>
        </div>
      </div>
      
      {/* Performance indicators */}
      <div className="mt-4 flex items-center justify-center gap-6 text-xs text-gray-500 dark:text-gray-400">
        <div className="flex items-center gap-1">
          <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
          <span>Live Data</span>
        </div>
        <div>
          Last updated: {new Date().toLocaleTimeString()}
        </div>
        <div>
          Data points: {data.length}/20
        </div>
      </div>
    </motion.div>
  );
}