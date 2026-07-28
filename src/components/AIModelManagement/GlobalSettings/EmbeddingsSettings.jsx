import React from 'react';

export default function EmbeddingsSettings({ settings, setSettings }) {
  return (
    <div className="grid grid-cols-2 gap-6">
      <div>
        <h3 className="text-lg font-semibold mb-4">Embeddings Model Settings</h3>

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
              <option value="nomic-ai/nomic-embed-text-v1.5">Nomic Embed Text v1.5 (768 dim)</option>
              <option value="BAAI/bge-base-en-v1.5">BGE Base EN v1.5 (768 dim)</option>
              <option value="BAAI/bge-large-en-v1.5">BGE Large EN v1.5 (1024 dim)</option>
              <option value="BAAI/bge-small-en-v1.5">BGE Small EN v1.5 (384 dim)</option>
              <option value="sentence-transformers/all-MiniLM-L6-v2">All-MiniLM-L6-v2 (384 dim)</option>
              <option value="sentence-transformers/all-mpnet-base-v2">All-MPNet-Base-v2 (768 dim)</option>
              <option value="thenlper/gte-large">GTE Large (1024 dim)</option>
              <option value="thenlper/gte-base">GTE Base (768 dim)</option>
              <option value="thenlper/gte-small">GTE Small (384 dim)</option>
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
              <option value={512}>512 tokens</option>
              <option value={1024}>1024 tokens</option>
              <option value={2048}>2048 tokens</option>
              <option value={4096}>4096 tokens</option>
              <option value={8192}>8192 tokens</option>
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

          <div className="space-y-2">
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={settings.normalize}
                onChange={(e) => setSettings({
                  ...settings,
                  normalize: e.target.checked
                })}
                className="rounded"
              />
              <span className="text-sm">Normalize embeddings (L2 normalization)</span>
            </label>

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
