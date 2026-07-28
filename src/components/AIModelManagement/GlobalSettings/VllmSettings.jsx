import React from 'react';

export default function VllmSettings({ settings, setSettings }) {
  return (
    <div className="grid grid-cols-2 gap-6">
      <div>
        <h3 className="text-lg font-semibold mb-4">GPU Settings</h3>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2">
              GPU Memory Utilization
            </label>
            <input
              type="range"
              min="0.1"
              max="1.0"
              step="0.05"
              value={settings.gpu_memory_utilization}
              onChange={(e) => setSettings({
                ...settings,
                gpu_memory_utilization: parseFloat(e.target.value)
              })}
              className="w-full"
            />
            <span className="text-sm text-gray-600 dark:text-gray-400">
              {(settings.gpu_memory_utilization * 100).toFixed(0)}%
            </span>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">
              Tensor Parallel Size
            </label>
            <select
              value={settings.tensor_parallel_size}
              onChange={(e) => setSettings({
                ...settings,
                tensor_parallel_size: parseInt(e.target.value)
              })}
              className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
            >
              <option value={1}>1 (Single GPU)</option>
              <option value={2}>2 GPUs</option>
              <option value={4}>4 GPUs</option>
              <option value={8}>8 GPUs</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">
              CPU Offload (GB)
            </label>
            <input
              type="number"
              min="0"
              max="64"
              value={settings.cpu_offload_gb}
              onChange={(e) => setSettings({
                ...settings,
                cpu_offload_gb: parseInt(e.target.value)
              })}
              className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
            />
          </div>
        </div>
      </div>

      <div>
        <h3 className="text-lg font-semibold mb-4">Model Settings</h3>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2">
              Max Model Length
            </label>
            <select
              value={settings.max_model_len}
              onChange={(e) => setSettings({
                ...settings,
                max_model_len: parseInt(e.target.value)
              })}
              className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
            >
              <option value={2048}>2K</option>
              <option value={4096}>4K</option>
              <option value={8192}>8K</option>
              <option value={16384}>16K</option>
              <option value={32768}>32K</option>
              <option value={65536}>64K</option>
              <option value={131072}>128K</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">
              Quantization
            </label>
            <select
              value={settings.quantization}
              onChange={(e) => setSettings({
                ...settings,
                quantization: e.target.value
              })}
              className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
            >
              <option value="auto">Auto-detect</option>
              <option value="awq">AWQ</option>
              <option value="gptq">GPTQ</option>
              <option value="squeezellm">SqueezeLLM</option>
              <option value="fp8">FP8</option>
              <option value="none">None (FP16)</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">
              Data Type
            </label>
            <select
              value={settings.dtype}
              onChange={(e) => setSettings({
                ...settings,
                dtype: e.target.value
              })}
              className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
            >
              <option value="auto">Auto</option>
              <option value="half">FP16</option>
              <option value="float16">float16</option>
              <option value="bfloat16">bfloat16</option>
              <option value="float">FP32</option>
            </select>
          </div>
        </div>
      </div>

      <div className="col-span-2">
        <h3 className="text-lg font-semibold mb-4">Advanced Settings</h3>

        <div className="grid grid-cols-3 gap-4">
          <div>
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={settings.trust_remote_code}
                onChange={(e) => setSettings({
                  ...settings,
                  trust_remote_code: e.target.checked
                })}
                className="rounded"
              />
              <span className="text-sm">Trust Remote Code</span>
            </label>
          </div>

          <div>
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={settings.enforce_eager}
                onChange={(e) => setSettings({
                  ...settings,
                  enforce_eager: e.target.checked
                })}
                className="rounded"
              />
              <span className="text-sm">Enforce Eager Mode</span>
            </label>
          </div>

          <div>
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={settings.disable_log_stats}
                onChange={(e) => setSettings({
                  ...settings,
                  disable_log_stats: e.target.checked
                })}
                className="rounded"
              />
              <span className="text-sm">Disable Log Stats</span>
            </label>
          </div>
        </div>
      </div>
    </div>
  );
}
