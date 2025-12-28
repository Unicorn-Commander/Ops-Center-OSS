import React, { useState } from 'react';
import {
  PlayIcon,
  DocumentTextIcon,
  CodeBracketIcon,
  ClockIcon
} from '@heroicons/react/24/outline';
import { useTheme } from '../contexts/ThemeContext';

const ApiPlayground = () => {
  const { currentTheme } = useTheme();
  const isDark = currentTheme === 'dark' || currentTheme === 'unicorn';

  const [method, setMethod] = useState('GET');
  const [endpoint, setEndpoint] = useState('/api/v1/system/status');
  const [headers, setHeaders] = useState(`Authorization: Bearer YOUR_TOKEN\nContent-Type: application/json`);
  const [body, setBody] = useState('{}');
  const [response, setResponse] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSendRequest = async () => {
    setLoading(true);
    setError(null);

    try {
      const token = localStorage.getItem('authToken');
      const headersObj = {};

      headers.split('\n').forEach(line => {
        const [key, ...valueParts] = line.split(':');
        if (key && valueParts.length) {
          headersObj[key.trim()] = valueParts.join(':').trim().replace('YOUR_TOKEN', token);
        }
      });

      const options = {
        method,
        headers: headersObj
      };

      if (method !== 'GET' && body.trim()) {
        try {
          options.body = body;
        } catch (e) {
          throw new Error('Invalid JSON in request body');
        }
      }

      const startTime = Date.now();
      const res = await fetch(endpoint, options);
      const duration = Date.now() - startTime;

      const responseData = await res.json();

      setResponse({
        status: res.status,
        statusText: res.statusText,
        headers: Object.fromEntries(res.headers.entries()),
        data: responseData,
        duration
      });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className={`text-2xl font-bold ${isDark ? 'text-white' : 'text-gray-900'} mb-2`}>
          <PlayIcon className="inline-block w-6 h-6 mr-2 mb-1" />
          API Playground
        </h2>
        <p className={isDark ? 'text-gray-300' : 'text-gray-600'}>
          Test API endpoints interactively in your browser.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Request Panel */}
        <div className={`rounded-lg border p-6 ${isDark ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
          <h3 className={`text-lg font-semibold ${isDark ? 'text-white' : 'text-gray-900'} mb-4`}>
            Request
          </h3>

          {/* Method & Endpoint */}
          <div className="space-y-4">
            <div className="flex gap-2">
              <select
                value={method}
                onChange={(e) => setMethod(e.target.value)}
                className={`px-3 py-2 rounded-lg border ${isDark ? 'bg-gray-700 border-gray-600 text-white' : 'bg-white border-gray-300 text-gray-900'}`}
              >
                <option>GET</option>
                <option>POST</option>
                <option>PUT</option>
                <option>DELETE</option>
              </select>

              <input
                type="text"
                value={endpoint}
                onChange={(e) => setEndpoint(e.target.value)}
                placeholder="/api/v1/..."
                className={`flex-1 px-3 py-2 rounded-lg border ${isDark ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400' : 'bg-white border-gray-300 text-gray-900 placeholder-gray-500'}`}
              />
            </div>

            {/* Headers */}
            <div>
              <label className={`block text-sm font-medium ${isDark ? 'text-gray-300' : 'text-gray-700'} mb-2`}>
                Headers
              </label>
              <textarea
                value={headers}
                onChange={(e) => setHeaders(e.target.value)}
                rows={3}
                className={`w-full px-3 py-2 rounded-lg border font-mono text-sm ${isDark ? 'bg-gray-700 border-gray-600 text-white' : 'bg-white border-gray-300 text-gray-900'}`}
              />
            </div>

            {/* Request Body */}
            {method !== 'GET' && (
              <div>
                <label className={`block text-sm font-medium ${isDark ? 'text-gray-300' : 'text-gray-700'} mb-2`}>
                  Request Body (JSON)
                </label>
                <textarea
                  value={body}
                  onChange={(e) => setBody(e.target.value)}
                  rows={6}
                  className={`w-full px-3 py-2 rounded-lg border font-mono text-sm ${isDark ? 'bg-gray-700 border-gray-600 text-white' : 'bg-white border-gray-300 text-gray-900'}`}
                />
              </div>
            )}

            {/* Send Button */}
            <button
              onClick={handleSendRequest}
              disabled={loading}
              className={`w-full px-4 py-2 rounded-lg font-semibold transition-colors flex items-center justify-center gap-2 ${loading ? 'opacity-50 cursor-not-allowed' : ''} ${isDark ? 'bg-purple-600 hover:bg-purple-700 text-white' : 'bg-blue-600 hover:bg-blue-700 text-white'}`}
            >
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent"></div>
                  Sending...
                </>
              ) : (
                <>
                  <PlayIcon className="w-5 h-5" />
                  Send Request
                </>
              )}
            </button>
          </div>
        </div>

        {/* Response Panel */}
        <div className={`rounded-lg border p-6 ${isDark ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
          <h3 className={`text-lg font-semibold ${isDark ? 'text-white' : 'text-gray-900'} mb-4`}>
            Response
          </h3>

          {error && (
            <div className="p-4 rounded-lg bg-red-500/10 border border-red-500 text-red-400 mb-4">
              <strong>Error:</strong> {error}
            </div>
          )}

          {response && (
            <div className="space-y-4">
              {/* Status */}
              <div className="flex items-center justify-between">
                <span className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>Status</span>
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${response.status < 300 ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}`}>
                  {response.status} {response.statusText}
                </span>
              </div>

              {/* Duration */}
              <div className="flex items-center justify-between">
                <span className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>Duration</span>
                <span className={`text-sm ${isDark ? 'text-gray-300' : 'text-gray-700'} flex items-center gap-1`}>
                  <ClockIcon className="w-4 h-4" />
                  {response.duration}ms
                </span>
              </div>

              {/* Response Body */}
              <div>
                <label className={`block text-sm font-medium ${isDark ? 'text-gray-300' : 'text-gray-700'} mb-2`}>
                  Response Body
                </label>
                <pre className={`p-4 rounded-lg overflow-x-auto text-sm font-mono ${isDark ? 'bg-gray-900 text-gray-300' : 'bg-gray-50 text-gray-800'}`}>
                  {JSON.stringify(response.data, null, 2)}
                </pre>
              </div>
            </div>
          )}

          {!response && !error && (
            <div className={`text-center py-12 ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
              <CodeBracketIcon className="w-12 h-12 mx-auto mb-3 opacity-50" />
              <p>Send a request to see the response here</p>
            </div>
          )}
        </div>
      </div>

      {/* Saved Requests (Future Enhancement) */}
      <div className={`p-4 rounded-lg border ${isDark ? 'bg-gray-800/50 border-gray-700' : 'bg-gray-50 border-gray-200'}`}>
        <h4 className={`text-sm font-semibold ${isDark ? 'text-gray-300' : 'text-gray-700'} mb-2`}>
          💡 Pro Tip
        </h4>
        <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Your authentication token is automatically inserted from localStorage. Use "YOUR_TOKEN" as a placeholder.
        </p>
      </div>
    </div>
  );
};

export default ApiPlayground;
