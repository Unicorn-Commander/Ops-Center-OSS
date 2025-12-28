import React, { useState, useEffect } from 'react';

export default function ModelSettingsForm({ 
  modelId, 
  activeTab, 
  globalSettings, 
  existingOverrides = {},
  onSave,
  onCancel 
}) {
  // Initialize state with existing overrides or empty values
  const [overrides, setOverrides] = useState(existingOverrides);

  if (activeTab === 'vllm') {
    return (
      <div className="grid grid-cols-2 gap-6">
        <div>
          <h3 className="text-lg font-semibold mb-4">GPU Settings Override</h3>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">
                GPU Memory Utilization
                {overrides.gpu_memory_utilization !== undefined && 
                  <span className="text-xs text-purple-600 dark:text-purple-400 ml-2">
                    (Overrides global: {(globalSettings.gpu_memory_utilization * 100).toFixed(0)}%)
                  </span>
                }
              </label>
              <div className="flex items-center gap-3">
                <input
                  type="range"
                  min="0.1"
                  max="1.0"
                  step="0.05"
                  value={overrides.gpu_memory_utilization || globalSettings.gpu_memory_utilization}
                  onChange={(e) => setOverrides({
                    ...overrides,
                    gpu_memory_utilization: parseFloat(e.target.value)
                  })}
                  className="flex-1"
                />
                <span className="text-sm text-gray-600 dark:text-gray-400 w-12">
                  {((overrides.gpu_memory_utilization || globalSettings.gpu_memory_utilization) * 100).toFixed(0)}%
                </span>
                <button
                  onClick={() => {
                    const newOverrides = { ...overrides };
                    delete newOverrides.gpu_memory_utilization;
                    setOverrides(newOverrides);
                  }}
                  className="text-xs text-gray-500 hover:text-gray-700"
                  title="Use global default"
                >
                  Reset
                </button>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">
                Tensor Parallel Size
                {overrides.tensor_parallel_size !== undefined && 
                  <span className="text-xs text-purple-600 dark:text-purple-400 ml-2">
                    (Overrides global: {globalSettings.tensor_parallel_size})
                  </span>
                }
              </label>
              <div className="flex items-center gap-3">
                <select
                  value={overrides.tensor_parallel_size || globalSettings.tensor_parallel_size}
                  onChange={(e) => setOverrides({
                    ...overrides,
                    tensor_parallel_size: parseInt(e.target.value)
                  })}
                  className="flex-1 px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
                >
                  <option value={1}>1 (Single GPU)</option>
                  <option value={2}>2 GPUs</option>
                  <option value={4}>4 GPUs</option>
                  <option value={8}>8 GPUs</option>
                </select>
                <button
                  onClick={() => {
                    const newOverrides = { ...overrides };
                    delete newOverrides.tensor_parallel_size;
                    setOverrides(newOverrides);
                  }}
                  className="text-xs text-gray-500 hover:text-gray-700"
                  title="Use global default"
                >
                  Reset
                </button>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">
                CPU Offload (GB)
                {overrides.cpu_offload_gb !== undefined && 
                  <span className="text-xs text-purple-600 dark:text-purple-400 ml-2">
                    (Overrides global: {globalSettings.cpu_offload_gb}GB)
                  </span>
                }
              </label>
              <div className="flex items-center gap-3">
                <input
                  type="number"
                  min="0"
                  max="64"
                  value={overrides.cpu_offload_gb !== undefined ? overrides.cpu_offload_gb : globalSettings.cpu_offload_gb}
                  onChange={(e) => setOverrides({
                    ...overrides,
                    cpu_offload_gb: parseInt(e.target.value)
                  })}
                  className="flex-1 px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
                />
                <button
                  onClick={() => {
                    const newOverrides = { ...overrides };
                    delete newOverrides.cpu_offload_gb;
                    setOverrides(newOverrides);
                  }}
                  className="text-xs text-gray-500 hover:text-gray-700"
                  title="Use global default"
                >
                  Reset
                </button>
              </div>
            </div>
          </div>
        </div>

        <div>
          <h3 className="text-lg font-semibold mb-4">Model Settings Override</h3>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">
                Max Model Length
                {overrides.max_model_len !== undefined && 
                  <span className="text-xs text-purple-600 dark:text-purple-400 ml-2">
                    (Overrides global: {globalSettings.max_model_len})
                  </span>
                }
              </label>
              <div className="flex items-center gap-3">
                <select
                  value={overrides.max_model_len || globalSettings.max_model_len}
                  onChange={(e) => setOverrides({
                    ...overrides,
                    max_model_len: parseInt(e.target.value)
                  })}
                  className="flex-1 px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
                >
                  <option value={2048}>2K</option>
                  <option value={4096}>4K</option>
                  <option value={8192}>8K</option>
                  <option value={16384}>16K</option>
                  <option value={32768}>32K</option>
                  <option value={65536}>64K</option>
                  <option value={131072}>128K</option>
                </select>
                <button
                  onClick={() => {
                    const newOverrides = { ...overrides };
                    delete newOverrides.max_model_len;
                    setOverrides(newOverrides);
                  }}
                  className="text-xs text-gray-500 hover:text-gray-700"
                  title="Use global default"
                >
                  Reset
                </button>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">
                Quantization
                {overrides.quantization !== undefined && 
                  <span className="text-xs text-purple-600 dark:text-purple-400 ml-2">
                    (Overrides global: {globalSettings.quantization})
                  </span>
                }
              </label>
              <div className="flex items-center gap-3">
                <select
                  value={overrides.quantization || globalSettings.quantization}
                  onChange={(e) => setOverrides({
                    ...overrides,
                    quantization: e.target.value
                  })}
                  className="flex-1 px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
                >
                  <option value="auto">Auto-detect</option>
                  <option value="awq">AWQ</option>
                  <option value="gptq">GPTQ</option>
                  <option value="squeezellm">SqueezeLLM</option>
                  <option value="fp8">FP8</option>
                  <option value="none">None (FP16)</option>
                </select>
                <button
                  onClick={() => {
                    const newOverrides = { ...overrides };
                    delete newOverrides.quantization;
                    setOverrides(newOverrides);
                  }}
                  className="text-xs text-gray-500 hover:text-gray-700"
                  title="Use global default"
                >
                  Reset
                </button>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">
                Data Type
                {overrides.dtype !== undefined && 
                  <span className="text-xs text-purple-600 dark:text-purple-400 ml-2">
                    (Overrides global: {globalSettings.dtype})
                  </span>
                }
              </label>
              <div className="flex items-center gap-3">
                <select
                  value={overrides.dtype || globalSettings.dtype}
                  onChange={(e) => setOverrides({
                    ...overrides,
                    dtype: e.target.value
                  })}
                  className="flex-1 px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
                >
                  <option value="auto">Auto</option>
                  <option value="half">FP16</option>
                  <option value="float16">float16</option>
                  <option value="bfloat16">bfloat16</option>
                  <option value="float">FP32</option>
                </select>
                <button
                  onClick={() => {
                    const newOverrides = { ...overrides };
                    delete newOverrides.dtype;
                    setOverrides(newOverrides);
                  }}
                  className="text-xs text-gray-500 hover:text-gray-700"
                  title="Use global default"
                >
                  Reset
                </button>
              </div>
            </div>
          </div>
        </div>

        <div className="col-span-2">
          <h3 className="text-lg font-semibold mb-4">Advanced Settings Override</h3>
          
          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={overrides.trust_remote_code !== undefined ? overrides.trust_remote_code : globalSettings.trust_remote_code}
                  onChange={(e) => setOverrides({
                    ...overrides,
                    trust_remote_code: e.target.checked
                  })}
                  className="rounded"
                />
                <span className="text-sm">Trust Remote Code</span>
                {overrides.trust_remote_code !== undefined && (
                  <button
                    onClick={() => {
                      const newOverrides = { ...overrides };
                      delete newOverrides.trust_remote_code;
                      setOverrides(newOverrides);
                    }}
                    className="text-xs text-gray-500 hover:text-gray-700 ml-2"
                  >
                    Reset
                  </button>
                )}
              </label>
            </div>

            <div>
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={overrides.enforce_eager !== undefined ? overrides.enforce_eager : globalSettings.enforce_eager}
                  onChange={(e) => setOverrides({
                    ...overrides,
                    enforce_eager: e.target.checked
                  })}
                  className="rounded"
                />
                <span className="text-sm">Enforce Eager Mode</span>
                {overrides.enforce_eager !== undefined && (
                  <button
                    onClick={() => {
                      const newOverrides = { ...overrides };
                      delete newOverrides.enforce_eager;
                      setOverrides(newOverrides);
                    }}
                    className="text-xs text-gray-500 hover:text-gray-700 ml-2"
                  >
                    Reset
                  </button>
                )}
              </label>
            </div>

            <div>
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={overrides.disable_log_stats !== undefined ? overrides.disable_log_stats : globalSettings.disable_log_stats}
                  onChange={(e) => setOverrides({
                    ...overrides,
                    disable_log_stats: e.target.checked
                  })}
                  className="rounded"
                />
                <span className="text-sm">Disable Log Stats</span>
                {overrides.disable_log_stats !== undefined && (
                  <button
                    onClick={() => {
                      const newOverrides = { ...overrides };
                      delete newOverrides.disable_log_stats;
                      setOverrides(newOverrides);
                    }}
                    className="text-xs text-gray-500 hover:text-gray-700 ml-2"
                  >
                    Reset
                  </button>
                )}
              </label>
            </div>
          </div>
        </div>

        <div className="col-span-2 mt-4">
          <div className="bg-gray-50 dark:bg-gray-700/50 p-4 rounded-lg">
            <h4 className="text-sm font-medium mb-2">Override Summary</h4>
            <div className="text-xs text-gray-600 dark:text-gray-400">
              {Object.keys(overrides).length === 0 ? (
                <p>No overrides set. This model will use all global settings.</p>
              ) : (
                <div>
                  <p className="mb-1">This model has {Object.keys(overrides).length} custom setting{Object.keys(overrides).length > 1 ? 's' : ''}:</p>
                  <ul className="list-disc list-inside ml-2">
                    {Object.entries(overrides).map(([key, value]) => (
                      <li key={key}>
                        {key.replace(/_/g, ' ')}: {typeof value === 'boolean' ? (value ? 'Enabled' : 'Disabled') : value}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="col-span-2 flex justify-end gap-2 mt-6">
          <button
            onClick={onCancel}
            className="px-4 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600"
          >
            Cancel
          </button>
          <button
            onClick={() => {
              // Only save non-empty overrides
              const cleanedOverrides = Object.entries(overrides).reduce((acc, [key, value]) => {
                if (value !== undefined) {
                  acc[key] = value;
                }
                return acc;
              }, {});
              onSave(modelId, cleanedOverrides);
            }}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Save Model Settings
          </button>
        </div>
      </div>
    );
  }

  // Ollama settings
  return (
    <div className="grid grid-cols-2 gap-6">
      <div>
        <h3 className="text-lg font-semibold mb-4">Performance Settings Override</h3>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2">
              GPU Layers
              {overrides.gpu_layers !== undefined && 
                <span className="text-xs text-purple-600 dark:text-purple-400 ml-2">
                  (Overrides global: {globalSettings.gpu_layers})
                </span>
              }
            </label>
            <div className="flex items-center gap-3">
              <input
                type="number"
                min="-1"
                value={overrides.gpu_layers !== undefined ? overrides.gpu_layers : globalSettings.gpu_layers}
                onChange={(e) => setOverrides({
                  ...overrides,
                  gpu_layers: parseInt(e.target.value)
                })}
                className="flex-1 px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
              />
              <button
                onClick={() => {
                  const newOverrides = { ...overrides };
                  delete newOverrides.gpu_layers;
                  setOverrides(newOverrides);
                }}
                className="text-xs text-gray-500 hover:text-gray-700"
                title="Use global default"
              >
                Reset
              </button>
            </div>
            <span className="text-xs text-gray-500">-1 = use all layers</span>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">
              Context Size
              {overrides.context_size !== undefined && 
                <span className="text-xs text-purple-600 dark:text-purple-400 ml-2">
                  (Overrides global: {globalSettings.context_size})
                </span>
              }
            </label>
            <div className="flex items-center gap-3">
              <select
                value={overrides.context_size || globalSettings.context_size}
                onChange={(e) => setOverrides({
                  ...overrides,
                  context_size: parseInt(e.target.value)
                })}
                className="flex-1 px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
              >
                <option value={512}>512</option>
                <option value={1024}>1024</option>
                <option value={2048}>2048</option>
                <option value={4096}>4096</option>
                <option value={8192}>8192</option>
                <option value={16384}>16384</option>
              </select>
              <button
                onClick={() => {
                  const newOverrides = { ...overrides };
                  delete newOverrides.context_size;
                  setOverrides(newOverrides);
                }}
                className="text-xs text-gray-500 hover:text-gray-700"
                title="Use global default"
              >
                Reset
              </button>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">
              CPU Threads
              {overrides.num_thread !== undefined && 
                <span className="text-xs text-purple-600 dark:text-purple-400 ml-2">
                  (Overrides global: {globalSettings.num_thread})
                </span>
              }
            </label>
            <div className="flex items-center gap-3">
              <input
                type="number"
                min="0"
                value={overrides.num_thread !== undefined ? overrides.num_thread : globalSettings.num_thread}
                onChange={(e) => setOverrides({
                  ...overrides,
                  num_thread: parseInt(e.target.value)
                })}
                className="flex-1 px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
              />
              <button
                onClick={() => {
                  const newOverrides = { ...overrides };
                  delete newOverrides.num_thread;
                  setOverrides(newOverrides);
                }}
                className="text-xs text-gray-500 hover:text-gray-700"
                title="Use global default"
              >
                Reset
              </button>
            </div>
            <span className="text-xs text-gray-500">0 = auto-detect</span>
          </div>
        </div>
      </div>

      <div>
        <h3 className="text-lg font-semibold mb-4">Generation Settings Override</h3>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2">
              Temperature
              {overrides.temperature !== undefined && 
                <span className="text-xs text-purple-600 dark:text-purple-400 ml-2">
                  (Overrides global: {globalSettings.temperature})
                </span>
              }
            </label>
            <div className="flex items-center gap-3">
              <input
                type="range"
                min="0"
                max="2"
                step="0.1"
                value={overrides.temperature !== undefined ? overrides.temperature : globalSettings.temperature}
                onChange={(e) => setOverrides({
                  ...overrides,
                  temperature: parseFloat(e.target.value)
                })}
                className="flex-1"
              />
              <span className="text-sm text-gray-600 dark:text-gray-400 w-8">
                {(overrides.temperature !== undefined ? overrides.temperature : globalSettings.temperature).toFixed(1)}
              </span>
              <button
                onClick={() => {
                  const newOverrides = { ...overrides };
                  delete newOverrides.temperature;
                  setOverrides(newOverrides);
                }}
                className="text-xs text-gray-500 hover:text-gray-700"
                title="Use global default"
              >
                Reset
              </button>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">
              Top K
              {overrides.top_k !== undefined && 
                <span className="text-xs text-purple-600 dark:text-purple-400 ml-2">
                  (Overrides global: {globalSettings.top_k})
                </span>
              }
            </label>
            <div className="flex items-center gap-3">
              <input
                type="number"
                min="1"
                max="100"
                value={overrides.top_k !== undefined ? overrides.top_k : globalSettings.top_k}
                onChange={(e) => setOverrides({
                  ...overrides,
                  top_k: parseInt(e.target.value)
                })}
                className="flex-1 px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
              />
              <button
                onClick={() => {
                  const newOverrides = { ...overrides };
                  delete newOverrides.top_k;
                  setOverrides(newOverrides);
                }}
                className="text-xs text-gray-500 hover:text-gray-700"
                title="Use global default"
              >
                Reset
              </button>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">
              Top P
              {overrides.top_p !== undefined && 
                <span className="text-xs text-purple-600 dark:text-purple-400 ml-2">
                  (Overrides global: {globalSettings.top_p})
                </span>
              }
            </label>
            <div className="flex items-center gap-3">
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={overrides.top_p !== undefined ? overrides.top_p : globalSettings.top_p}
                onChange={(e) => setOverrides({
                  ...overrides,
                  top_p: parseFloat(e.target.value)
                })}
                className="flex-1"
              />
              <span className="text-sm text-gray-600 dark:text-gray-400 w-8">
                {(overrides.top_p !== undefined ? overrides.top_p : globalSettings.top_p).toFixed(2)}
              </span>
              <button
                onClick={() => {
                  const newOverrides = { ...overrides };
                  delete newOverrides.top_p;
                  setOverrides(newOverrides);
                }}
                className="text-xs text-gray-500 hover:text-gray-700"
                title="Use global default"
              >
                Reset
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="col-span-2">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={overrides.use_mmap !== undefined ? overrides.use_mmap : globalSettings.use_mmap}
                onChange={(e) => setOverrides({
                  ...overrides,
                  use_mmap: e.target.checked
                })}
                className="rounded"
              />
              <span className="text-sm">Use Memory Mapping</span>
              {overrides.use_mmap !== undefined && (
                <button
                  onClick={() => {
                    const newOverrides = { ...overrides };
                    delete newOverrides.use_mmap;
                    setOverrides(newOverrides);
                  }}
                  className="text-xs text-gray-500 hover:text-gray-700 ml-2"
                >
                  Reset
                </button>
              )}
            </label>
          </div>

          <div>
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={overrides.use_mlock !== undefined ? overrides.use_mlock : globalSettings.use_mlock}
                onChange={(e) => setOverrides({
                  ...overrides,
                  use_mlock: e.target.checked
                })}
                className="rounded"
              />
              <span className="text-sm">Lock Model in RAM</span>
              {overrides.use_mlock !== undefined && (
                <button
                  onClick={() => {
                    const newOverrides = { ...overrides };
                    delete newOverrides.use_mlock;
                    setOverrides(newOverrides);
                  }}
                  className="text-xs text-gray-500 hover:text-gray-700 ml-2"
                >
                  Reset
                </button>
              )}
            </label>
          </div>
        </div>
      </div>

      <div className="col-span-2 mt-4">
        <div className="bg-gray-50 dark:bg-gray-700/50 p-4 rounded-lg">
          <h4 className="text-sm font-medium mb-2">Override Summary</h4>
          <div className="text-xs text-gray-600 dark:text-gray-400">
            {Object.keys(overrides).length === 0 ? (
              <p>No overrides set. This model will use all global settings.</p>
            ) : (
              <div>
                <p className="mb-1">This model has {Object.keys(overrides).length} custom setting{Object.keys(overrides).length > 1 ? 's' : ''}:</p>
                <ul className="list-disc list-inside ml-2">
                  {Object.entries(overrides).map(([key, value]) => (
                    <li key={key}>
                      {key.replace(/_/g, ' ')}: {typeof value === 'boolean' ? (value ? 'Enabled' : 'Disabled') : value}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="col-span-2 flex justify-end gap-2 mt-6">
        <button
          onClick={onCancel}
          className="px-4 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600"
        >
          Cancel
        </button>
        <button
          onClick={() => {
            // Only save non-empty overrides
            const cleanedOverrides = Object.entries(overrides).reduce((acc, [key, value]) => {
              if (value !== undefined) {
                acc[key] = value;
              }
              return acc;
            }, {});
            onSave(modelId, cleanedOverrides);
          }}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          Save Model Settings
        </button>
      </div>
    </div>
  );
}