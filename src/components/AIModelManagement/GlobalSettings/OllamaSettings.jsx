import React from 'react';

export default function OllamaSettings({ settings, setSettings }) {
  return (
    <div className="grid grid-cols-2 gap-6">
      <div>
        <h3 className="text-lg font-semibold mb-4">Performance Settings</h3>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2">
              GPU Layers
            </label>
            <input
              type="number"
              min="-1"
              value={settings.gpu_layers}
              onChange={(e) => setSettings({
                ...settings,
                gpu_layers: parseInt(e.target.value)
              })}
              className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
            />
            <span className="text-xs text-gray-500">-1 = use all layers</span>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">
              Context Size
            </label>
            <select
              value={settings.context_size}
              onChange={(e) => setSettings({
                ...settings,
                context_size: parseInt(e.target.value)
              })}
              className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
            >
              <option value={512}>512</option>
              <option value={1024}>1024</option>
              <option value={2048}>2048</option>
              <option value={4096}>4096</option>
              <option value={8192}>8192</option>
              <option value={16384}>16384</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">
              CPU Threads
            </label>
            <input
              type="number"
              min="0"
              value={settings.num_thread}
              onChange={(e) => setSettings({
                ...settings,
                num_thread: parseInt(e.target.value)
              })}
              className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
            />
            <span className="text-xs text-gray-500">0 = auto-detect</span>
          </div>
        </div>
      </div>

      <div>
        <h3 className="text-lg font-semibold mb-4">Generation Settings</h3>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2">
              Temperature ({settings.temperature})
            </label>
            <input
              type="range"
              min="0"
              max="2"
              step="0.1"
              value={settings.temperature}
              onChange={(e) => setSettings({
                ...settings,
                temperature: parseFloat(e.target.value)
              })}
              className="w-full"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">
              Top K
            </label>
            <input
              type="number"
              min="1"
              max="100"
              value={settings.top_k}
              onChange={(e) => setSettings({
                ...settings,
                top_k: parseInt(e.target.value)
              })}
              className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">
              Top P ({settings.top_p})
            </label>
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={settings.top_p}
              onChange={(e) => setSettings({
                ...settings,
                top_p: parseFloat(e.target.value)
              })}
              className="w-full"
            />
          </div>
        </div>
      </div>

      <div className="col-span-2">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={settings.use_mmap}
                onChange={(e) => setSettings({
                  ...settings,
                  use_mmap: e.target.checked
                })}
                className="rounded"
              />
              <span className="text-sm">Use Memory Mapping</span>
            </label>
          </div>

          <div>
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={settings.use_mlock}
                onChange={(e) => setSettings({
                  ...settings,
                  use_mlock: e.target.checked
                })}
                className="rounded"
              />
              <span className="text-sm">Lock Model in RAM</span>
            </label>
          </div>
        </div>
      </div>
    </div>
  );
}
