import React from 'react';

export default function RerankerSettings({ settings, setSettings }) {
  return (
    <div className="grid grid-cols-2 gap-6">
      <div>
        <h3 className="text-lg font-semibold mb-4">Reranker Model Settings</h3>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2">
              Current Model
            </label>
            <select
              value={settings.model_name}
              onChange={(e) => setSettings({
                ...settings,
                model_name: e.target.value
              })}
              className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
            >
              <option value="mixedbread-ai/mxbai-rerank-large-v1">MxBai Rerank Large v1</option>
              <option value="mixedbread-ai/mxbai-rerank-base-v1">MxBai Rerank Base v1</option>
              <option value="BAAI/bge-reranker-v2-m3">BGE Reranker v2 M3</option>
              <option value="BAAI/bge-reranker-large">BGE Reranker Large</option>
              <option value="BAAI/bge-reranker-base">BGE Reranker Base</option>
              <option value="cross-encoder/ms-marco-MiniLM-L-6-v2">MS-MARCO MiniLM L6 v2</option>
              <option value="cross-encoder/ms-marco-MiniLM-L-12-v2">MS-MARCO MiniLM L12 v2</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">
              Device
            </label>
            <select
              value={settings.device}
              onChange={(e) => setSettings({
                ...settings,
                device: e.target.value
              })}
              className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
            >
              <option value="cpu">CPU (Intel iGPU via OpenVINO)</option>
              <option value="cuda">CUDA (NVIDIA GPU)</option>
              <option value="mps">MPS (Apple Silicon)</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">
              Max Length
            </label>
            <select
              value={settings.max_length}
              onChange={(e) => setSettings({
                ...settings,
                max_length: parseInt(e.target.value)
              })}
              className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
            >
              <option value={256}>256 tokens</option>
              <option value={512}>512 tokens</option>
              <option value={1024}>1024 tokens</option>
              <option value={2048}>2048 tokens</option>
            </select>
          </div>
        </div>
      </div>

      <div>
        <h3 className="text-lg font-semibold mb-4">Performance Settings</h3>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2">
              Batch Size
            </label>
            <input
              type="number"
              min="1"
              max="128"
              value={settings.batch_size}
              onChange={(e) => setSettings({
                ...settings,
                batch_size: parseInt(e.target.value)
              })}
              className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">
              Model Cache Directory
            </label>
            <input
              type="text"
              value={settings.models_cache_dir}
              onChange={(e) => setSettings({
                ...settings,
                models_cache_dir: e.target.value
              })}
              className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
            />
          </div>

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
              <span className="text-sm">Trust remote code (required for some models)</span>
            </label>
          </div>
        </div>
      </div>
    </div>
  );
}
