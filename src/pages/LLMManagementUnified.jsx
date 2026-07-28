import React, { useState, useCallback, useMemo } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useTheme } from "../contexts/ThemeContext";
import { useToast } from "../components/Toast";
import {
  Brain, Search, Filter, DollarSign, RefreshCw,
  CheckCircle, XCircle, Zap, MessageSquare,
  Image as ImageIcon, Code2, Sparkles,
  ChevronDown, ChevronUp, LayoutGrid, List as ListIcon,
  Download, HardDrive, Globe, Server,
} from "lucide-react";
import { fetchFederationJson } from "../utils/federationApi";

const formatPrice = (price) => {
  if (price === 0) return "Free";
  if (price < 0.01) return `$${price.toFixed(6)}`;
  if (price < 1) return `$${price.toFixed(4)}`;
  return `$${price.toFixed(2)}`;
};

const ModelRow = ({ model, theme, onToggle }) => {
  if (!model) return null;
  const isLocal = model.source === "federation";
  const peerCount = model.peer_count || 1;

  return (
    <div className={`border-b ${theme?.border || "border-gray-700"} hover:bg-gray-800/50 transition-all`}>
      <div className="flex items-center gap-4 p-4">
        {/* Toggle Switch */}
        <div className="flex-shrink-0">
          <button
            onClick={() => onToggle(model.id)}
            className={`relative w-12 h-6 rounded-full transition-all ${
              model.is_active
                ? "bg-green-500 hover:bg-green-600"
                : "bg-gray-600 hover:bg-gray-500"
            }`}
          >
            <div
              className={`absolute top-1 w-4 h-4 bg-white rounded-full shadow-lg transition-all ${
                model.is_active ? "left-7" : "left-1"
              }`}
            />
          </button>
        </div>

        {/* Model Name & Provider */}
        <div className="flex-1 min-w-0">
          <div className={`font-medium ${theme?.text?.primary || "text-white"} truncate flex items-center gap-2`}>
            {model.name}
            {isLocal && (
              <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-bold bg-purple-500/20 text-purple-300">
                <HardDrive className="h-3 w-3" />
                LOCAL
              </span>
            )}
            {peerCount > 1 && (
              <span className="text-[10px] text-blue-400 bg-blue-500/10 px-1.5 py-0.5 rounded">
                {peerCount} peers
              </span>
            )}
          </div>
          <div className={`text-xs ${theme?.text?.secondary || "text-gray-400"} truncate mt-0.5`}>
            {model.id}
            {model.node_display && (
              <span className="ml-2 text-purple-400">@{model.node_display}</span>
            )}
          </div>
        </div>

        {/* Source badge */}
        <div className="flex-shrink-0">
          {isLocal ? (
            <span className="flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-medium bg-green-500/20 text-green-400">
              <Server className="h-3 w-3" /> Federation
            </span>
          ) : (
            <span className="flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-medium bg-blue-500/20 text-blue-400">
              <Globe className="h-3 w-3" /> Cloud
            </span>
          )}
        </div>

        {/* Capabilities */}
        <div className="flex items-center gap-2 flex-shrink-0">
          {model.supports_streaming && (
            <div className="p-1.5 rounded-lg bg-blue-500/20 text-blue-400" title="Streaming">
              <Zap className="h-3.5 w-3.5" />
            </div>
          )}
          {model.supports_function_calling && (
            <div className="p-1.5 rounded-lg bg-purple-500/20 text-purple-400" title="Function Calling">
              <Code2 className="h-3.5 w-3.5" />
            </div>
          )}
          {model.supports_vision && (
            <div className="p-1.5 rounded-lg bg-pink-500/20 text-pink-400" title="Vision">
              <ImageIcon className="h-3.5 w-3.5" />
            </div>
          )}
        </div>

        {/* Context Length */}
        <div className="text-right flex-shrink-0 min-w-[80px]">
          <div className={`text-sm ${theme?.text?.primary || "text-white"}`}>
            {((model.context_length || 0) / 1000).toFixed(0)}K
          </div>
          <div className={`text-xs ${theme?.text?.secondary || "text-gray-400"}`}>tokens</div>
        </div>

        {/* Pricing */}
        <div className="text-right flex-shrink-0 min-w-[100px]">
          <div className={`text-sm font-medium ${theme?.text?.primary || "text-white"}`}>
            {formatPrice(model.pricing?.prompt_per_1m || 0)}
          </div>
          <div className={`text-xs ${theme?.text?.secondary || "text-gray-400"}`}>per 1M in</div>
        </div>
        <div className="text-right flex-shrink-0 min-w-[100px]">
          <div className={`text-sm font-medium ${theme?.text?.primary || "text-white"}`}>
            {formatPrice(model.pricing?.completion_per_1m || 0)}
          </div>
          <div className={`text-xs ${theme?.text?.secondary || "text-gray-400"}`}>per 1M out</div>
        </div>

        {/* Status */}
        <div className="flex-shrink-0">
          {model.is_active ? (
            <CheckCircle className="h-5 w-5 text-green-500" />
          ) : (
            <XCircle className="h-5 w-5 text-gray-500" />
          )}
        </div>
      </div>
    </div>
  );
};

const buildFederationModels = (services) => {
  if (!services || services.length === 0) return [];
  const modelMap = new Map();

  for (const svc of services) {
    if (svc.node_status === "offline") continue;
    const models = svc.models || [];
    for (const m of models) {
      const key = m.toLowerCase();
      if (modelMap.has(key)) {
        const existing = modelMap.get(key);
        existing.peer_count = (existing.peer_count || 1) + 1;
        existing.node_ids = [...(existing.node_ids || []), svc.node_id];
        continue;
      }
      modelMap.set(key, {
        id: `federation:${key}`,
        name: m,
        source: "federation",
        is_active: true,
        node_id: svc.node_id,
        node_display: svc.display_name || svc.node_id,
        node_ids: [svc.node_id],
        peer_count: 1,
        context_length: svc.capabilities?.max_context || 8192,
        supports_streaming: true,
        supports_function_calling: svc.capabilities?.function_calling || false,
        supports_vision: false,
        pricing: {
          prompt_per_1m: svc.cost_usd || 0,
          completion_per_1m: svc.cost_usd || 0,
        },
      });
    }
  }
  return Array.from(modelMap.values());
};

export default function LLMManagementUnified() {
  const { theme } = useTheme();
  const { showToast } = useToast();
  const queryClient = useQueryClient();

  const [searchTerm, setSearchTerm] = useState("");
  const [filterActive, setFilterActive] = useState("all");
  const [sortBy, setSortBy] = useState("name");
  const [showFilters, setShowFilters] = useState(false);
  const [filterSource, setFilterSource] = useState("all");

  const { data: openrouterData, isLoading: isORLoading, error: orError } = useQuery({
    queryKey: ["openrouter-models"],
    queryFn: async () => {
      const response = await fetch("/api/v1/llm/admin/models/openrouter", {
        credentials: "include",
      });
      if (!response.ok) throw new Error("Failed to fetch OpenRouter models");
      return response.json();
    },
    staleTime: 5 * 60 * 1000,
  });

  const { data: federationData, isLoading: isFedLoading } = useQuery({
    queryKey: ["federation-llm-services"],
    queryFn: async () => {
      const data = await fetchFederationJson(
        "/api/v1/federation/services?service_type=llm"
      );
      return data.services || [];
    },
    staleTime: 30 * 1000,
  });

  const toggleMutation = useMutation({
    mutationFn: async (modelId) => {
      const response = await fetch(
        `/api/v1/llm/admin/models/${encodeURIComponent(modelId)}/toggle`,
        { method: "PUT", credentials: "include" }
      );
      if (!response.ok) throw new Error("Failed to toggle model");
      return response.json();
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries(["openrouter-models"]);
      showToast("success", data.message || "Model status updated");
    },
    onError: (error) => {
      showToast("error", error.message || "Failed to update model");
    },
  });

  const handleToggle = useCallback(
    (modelId) => {
      if (modelId.startsWith("federation:")) {
        showToast("info", "Federation models are always active while the peer is online");
        return;
      }
      toggleMutation.mutate(modelId);
    },
    [toggleMutation, showToast]
  );

  const allModels = useMemo(() => {
    const models = [];

    // Federation models first
    if (federationData && federationData.length > 0) {
      models.push(...buildFederationModels(federationData));
    }

    // OpenRouter + external models
    if (openrouterData?.models) {
      for (const m of openrouterData.models) {
        models.push({
          ...m,
          source: "cloud",
          node_display: m.provider || "OpenRouter",
        });
      }
    }

    return models;
  }, [federationData, openrouterData]);

  const filteredAndSortedModels = useMemo(() => {
    try {
      let filtered = [...allModels];

      if (searchTerm) {
        const search = searchTerm.toLowerCase();
        filtered = filtered.filter(
          (m) =>
            m.name?.toLowerCase().includes(search) ||
            m.id?.toLowerCase().includes(search) ||
            m.description?.toLowerCase().includes(search)
        );
      }

      if (filterActive === "enabled") {
        filtered = filtered.filter((m) => m.is_active);
      } else if (filterActive === "disabled") {
        filtered = filtered.filter((m) => !m.is_active);
      }

      if (filterSource === "federation") {
        filtered = filtered.filter((m) => m.source === "federation");
      } else if (filterSource === "cloud") {
        filtered = filtered.filter((m) => m.source !== "federation");
      }

      filtered.sort((a, b) => {
        switch (sortBy) {
          case "name":
            return (a.name || "").localeCompare(b.name || "");
          case "price_asc":
            return (a.pricing?.prompt_per_1m || 0) - (b.pricing?.prompt_per_1m || 0);
          case "price_desc":
            return (b.pricing?.prompt_per_1m || 0) - (a.pricing?.prompt_per_1m || 0);
          case "context":
            return (b.context_length || 0) - (a.context_length || 0);
          default:
            return 0;
        }
      });

      return filtered;
    } catch (err) {
      console.error("Error filtering models:", err);
      return [];
    }
  }, [allModels, searchTerm, filterActive, sortBy, filterSource]);

  const stats = useMemo(() => {
    const fedCount = allModels.filter((m) => m.source === "federation").length;
    const cloudCount = allModels.filter((m) => m.source !== "federation").length;
    const enabled = allModels.filter((m) => m.is_active).length;
    return {
      total: allModels.length,
      federation: fedCount,
      cloud: cloudCount,
      enabled,
      disabled: allModels.length - enabled,
    };
  }, [allModels]);

  const isLoading = isORLoading || isFedLoading;
  const error = orError;

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className={`text-3xl font-bold ${theme?.text?.primary || "text-white"} flex items-center gap-3`}>
            <div className="p-2 rounded-xl bg-gradient-to-br from-purple-500 to-pink-500">
              <Brain className="h-8 w-8 text-white" />
            </div>
            LLM Model Catalog
          </h1>
          <p className={`mt-2 ${theme?.text?.secondary || "text-gray-400"}`}>
            Federation models + OpenRouter & external providers
          </p>
        </div>
        <button
          onClick={() => {
            queryClient.invalidateQueries(["openrouter-models"]);
            queryClient.invalidateQueries(["federation-llm-services"]);
          }}
          disabled={isLoading}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg ${theme?.button?.secondary || "bg-gray-700"} transition-all ${
            isLoading ? "opacity-50 cursor-not-allowed" : "hover:opacity-80"
          }`}
        >
          <RefreshCw className={`h-4 w-4 ${isLoading ? "animate-spin" : ""}`} />
          <span>Refresh</span>
        </button>
      </div>

      {/* Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className={`${theme?.card || "bg-gray-800"} rounded-xl p-6 border border-purple-500/20`}>
          <div className="flex items-center justify-between">
            <div>
              <p className={`text-sm ${theme?.text?.secondary || "text-gray-400"}`}>Total Models</p>
              <p className={`text-3xl font-bold ${theme?.text?.primary || "text-white"} mt-1`}>{stats.total}</p>
            </div>
            <div className="p-3 rounded-lg bg-purple-500/20">
              <Brain className="h-6 w-6 text-purple-400" />
            </div>
          </div>
        </div>
        <div className={`${theme?.card || "bg-gray-800"} rounded-xl p-6 border border-green-500/20`}>
          <div className="flex items-center justify-between">
            <div>
              <p className={`text-sm ${theme?.text?.secondary || "text-gray-400"}`}>Federation (Local)</p>
              <p className={`text-3xl font-bold text-green-400 mt-1`}>{stats.federation}</p>
            </div>
            <div className="p-3 rounded-lg bg-green-500/20">
              <Server className="h-6 w-6 text-green-400" />
            </div>
          </div>
        </div>
        <div className={`${theme?.card || "bg-gray-800"} rounded-xl p-6 border border-blue-500/20`}>
          <div className="flex items-center justify-between">
            <div>
              <p className={`text-sm ${theme?.text?.secondary || "text-gray-400"}`}>Cloud Providers</p>
              <p className={`text-3xl font-bold text-blue-400 mt-1`}>{stats.cloud}</p>
            </div>
            <div className="p-3 rounded-lg bg-blue-500/20">
              <Globe className="h-6 w-6 text-blue-400" />
            </div>
          </div>
        </div>
        <div className={`${theme?.card || "bg-gray-800"} rounded-xl p-6 border border-gray-500/20`}>
          <div className="flex items-center justify-between">
            <div>
              <p className={`text-sm ${theme?.text?.secondary || "text-gray-400"}`}>Enabled</p>
              <p className={`text-3xl font-bold ${theme?.text?.primary || "text-white"} mt-1`}>{stats.enabled}</p>
            </div>
            <div className="p-3 rounded-lg bg-gray-500/20">
              <CheckCircle className="h-6 w-6 text-gray-400" />
            </div>
          </div>
        </div>
      </div>

      {/* Search & Filters */}
      <div className={`${theme?.card || "bg-gray-800"} rounded-xl p-4 space-y-4`}>
        <div className="flex items-center gap-4">
          <div className="flex-1 relative">
            <Search className={`absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 ${theme?.text?.secondary || "text-gray-400"}`} />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search models by name, ID, or description..."
              className={`w-full pl-10 pr-4 py-2 rounded-lg bg-gray-700/50 border border-gray-600 text-white focus:outline-none focus:ring-2 focus:ring-purple-500`}
            />
          </div>
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg bg-gray-700 hover:bg-gray-600 transition-all`}
          >
            <Filter className="h-4 w-4" />
            <span>Filters</span>
            {showFilters ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
          </button>
        </div>

        {showFilters && (
          <div className="overflow-hidden">
            <div className="flex items-center gap-4 pt-4 border-t border-gray-700">
              <div className="flex items-center gap-2">
                <span className={`text-sm ${theme?.text?.secondary || "text-gray-400"}`}>Status:</span>
                <select
                  value={filterActive}
                  onChange={(e) => setFilterActive(e.target.value)}
                  className="px-3 py-1.5 rounded-lg bg-gray-700 border border-gray-600 text-white text-sm"
                >
                  <option value="all">All Models</option>
                  <option value="enabled">Enabled Only</option>
                  <option value="disabled">Disabled Only</option>
                </select>
              </div>
              <div className="flex items-center gap-2">
                <span className={`text-sm ${theme?.text?.secondary || "text-gray-400"}`}>Source:</span>
                <select
                  value={filterSource}
                  onChange={(e) => setFilterSource(e.target.value)}
                  className="px-3 py-1.5 rounded-lg bg-gray-700 border border-gray-600 text-white text-sm"
                >
                  <option value="all">All Sources</option>
                  <option value="federation">Federation (Local)</option>
                  <option value="cloud">Cloud Providers</option>
                </select>
              </div>
              <div className="flex items-center gap-2">
                <span className={`text-sm ${theme?.text?.secondary || "text-gray-400"}`}>Sort:</span>
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value)}
                  className="px-3 py-1.5 rounded-lg bg-gray-700 border border-gray-600 text-white text-sm"
                >
                  <option value="name">Name (A-Z)</option>
                  <option value="price_asc">Price (Low to High)</option>
                  <option value="price_desc">Price (High to Low)</option>
                  <option value="context">Context Length</option>
                </select>
              </div>
              <div className="ml-auto">
                <span className={`text-sm ${theme?.text?.secondary || "text-gray-400"}`}>
                  Showing {filteredAndSortedModels.length} of {stats.total} models
                </span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Models Table */}
      <div className={`${theme?.card || "bg-gray-800"} rounded-xl overflow-hidden`}>
        <div className="border-b border-gray-700 p-4 font-medium">
          <div className="flex items-center gap-4">
            <div className="w-12 flex-shrink-0">
              <span className="text-xs text-gray-400">Status</span>
            </div>
            <div className="flex-1 min-w-0">
              <span className="text-xs text-gray-400">Model Name / Provider</span>
            </div>
            <div className="flex-shrink-0 min-w-[80px]">
              <span className="text-xs text-gray-400">Source</span>
            </div>
            <div className="flex items-center gap-2 flex-shrink-0">
              <span className="text-xs text-gray-400">Features</span>
            </div>
            <div className="text-right flex-shrink-0 min-w-[80px]">
              <span className="text-xs text-gray-400">Context</span>
            </div>
            <div className="text-right flex-shrink-0 min-w-[100px]">
              <span className="text-xs text-gray-400">Input Cost</span>
            </div>
            <div className="text-right flex-shrink-0 min-w-[100px]">
              <span className="text-xs text-gray-400">Output Cost</span>
            </div>
            <div className="flex-shrink-0 w-5"></div>
          </div>
        </div>

        {isLoading && (
          <div className="flex items-center justify-center py-12">
            <RefreshCw className="h-8 w-8 text-gray-400 animate-spin" />
          </div>
        )}

        {error && (
          <div className="flex flex-col items-center justify-center py-12">
            <XCircle className="h-12 w-12 text-red-500 mb-4" />
            <p className={`text-lg ${theme?.text?.primary || "text-white"} mb-2`}>Failed to load models</p>
            <p className={`text-sm ${theme?.text?.secondary || "text-gray-400"} mb-4`}>{error.message}</p>
            <button
              onClick={() => {
                queryClient.invalidateQueries(["openrouter-models"]);
                queryClient.invalidateQueries(["federation-llm-services"]);
              }}
              className="px-4 py-2 rounded-lg bg-purple-600 text-white"
            >
              Try Again
            </button>
          </div>
        )}

        {!isLoading && !error && filteredAndSortedModels.length > 0 && (
          <div className="max-h-[600px] overflow-y-auto">
            {filteredAndSortedModels.map((model) => (
              <ModelRow
                key={model.id}
                model={model}
                theme={theme}
                onToggle={handleToggle}
              />
            ))}
          </div>
        )}

        {!isLoading && !error && filteredAndSortedModels.length === 0 && (
          <div className="flex flex-col items-center justify-center py-12">
            <Search className="h-12 w-12 text-gray-400 mb-4" />
            <p className={`text-lg ${theme?.text?.primary || "text-white"} mb-2`}>No models found</p>
            <p className={`text-sm ${theme?.text?.secondary || "text-gray-400"}`}>
              Try adjusting your search or filters
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
