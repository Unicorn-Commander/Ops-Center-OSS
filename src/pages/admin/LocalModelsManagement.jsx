import React, { useState, useEffect, useCallback, useMemo } from "react";
import {
  Box, Paper, Typography, Button, Grid, Card, CardContent,
  Alert, CircularProgress, Chip, Divider, Switch, FormControlLabel,
  LinearProgress,
} from "@mui/material";
import {
  Refresh as RefreshIcon, Hub as HubIcon,
  CheckCircle as OnlineIcon, Cancel as OfflineIcon,
  Storage as ModelIcon, Dns as NodeIcon,
  Schedule as ScheduleIcon,
} from "@mui/icons-material";
import PageHeader from "../../components/admin/PageHeader";
import { fetchFederationJson, federationTimeAgo } from "../../utils/federationApi";

const API_BASE = "/api/v1/federation";

const LocalModelsManagement = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [services, setServices] = useState([]);
  const [refreshing, setRefreshing] = useState(false);
  const [includeOffline, setIncludeOffline] = useState(false);

  const fetchServices = useCallback(async () => {
    try {
      const data = await fetchFederationJson(
        `${API_BASE}/services?service_type=llm`
      );
      setServices(data.services || []);
      setError(null);
    } catch (err) {
      console.error("Failed to fetch federation LLM services:", err);
      setError(err.message);
    }
  }, []);

  useEffect(() => {
    fetchServices().finally(() => setLoading(false));
  }, [fetchServices]);

  useEffect(() => {
    const interval = setInterval(fetchServices, 30000);
    return () => clearInterval(interval);
  }, [fetchServices]);

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchServices();
    setRefreshing(false);
  };

  const filteredServices = useMemo(() => {
    if (includeOffline) return services;
    return services.filter((s) => s.node_status !== "offline");
  }, [services, includeOffline]);

  const onlineCount = services.filter((s) => s.node_status !== "offline").length;

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <PageHeader
        title="Federated LLM Services"
        subtitle="Live language model endpoints discovered across the Unicorn federation mesh"
        actions={
          <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
            <FormControlLabel
              control={
                <Switch
                  checked={includeOffline}
                  onChange={(e) => setIncludeOffline(e.target.checked)}
                  size="small"
                />
              }
              label="Show offline"
            />
            <Chip
              icon={<OnlineIcon />}
              label={`${onlineCount}/${services.length} online`}
              color={onlineCount === services.length ? "success" : onlineCount > 0 ? "warning" : "error"}
              variant="outlined"
            />
            <Button
              variant="outlined"
              startIcon={<RefreshIcon />}
              onClick={handleRefresh}
              disabled={refreshing}
            >
              Refresh
            </Button>
          </Box>
        }
      />

      {error && (
        <Alert severity="error" onClose={() => setError(null)} sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {filteredServices.length === 0 && (
        <Alert severity="warning" sx={{ mb: 2 }}>
          {services.length === 0
            ? "No federation peers found advertising LLM services. Check that federation agents are running on GPU nodes."
            : "All federation LLM services are offline. Try toggling Show offline to see disconnected peers."}
        </Alert>
      )}

      {filteredServices.map((svc, idx) => {
        const isOnline = svc.node_status !== "offline";
        const models = svc.models || [];
        const caps = svc.capabilities || {};

        return (
          <Paper key={`${svc.node_id}-${svc.service_type}-${idx}`} sx={{ p: 3, mb: 3, borderRadius: 2 }}>
            <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 2 }}>
              <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                <HubIcon sx={{ color: isOnline ? "success.main" : "text.disabled" }} />
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  {svc.display_name || svc.node_id}
                </Typography>
                <Chip
                  label={isOnline ? "Online" : "Offline"}
                  size="small"
                  color={isOnline ? "success" : "error"}
                />
                <Chip label={`Node: ${svc.node_id}`} size="small" variant="outlined" />
              </Box>
              <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                <ScheduleIcon sx={{ fontSize: 16, color: "text.secondary" }} />
                <Typography variant="caption" color="text.secondary">
                  {svc.last_heartbeat
                    ? `Last heartbeat: ${federationTimeAgo(svc.last_heartbeat)}`
                    : "No heartbeat"}
                </Typography>
              </Box>
            </Box>

            {svc.endpoint_url && (
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2, fontFamily: "monospace" }}>
                Endpoint: {svc.endpoint_url}{svc.endpoint_path || ""}
              </Typography>
            )}

            {caps.vram_mb && (
              <Box sx={{ mb: 2 }}>
                <Typography variant="caption" color="text.secondary">VRAM: {caps.vram_mb} MB</Typography>
                <LinearProgress
                  variant="determinate"
                  value={caps.vram_usage_pct || 0}
                  sx={{ height: 4, borderRadius: 2, mt: 0.5 }}
                />
              </Box>
            )}

            {models.length === 0 ? (
              <Alert severity="info">
                No models currently loaded on this node.
              </Alert>
            ) : (
              <Grid container spacing={1}>
                {models.map((model) => (
                  <Grid item key={model}>
                    <Chip
                      icon={<ModelIcon />}
                      label={model}
                      color="primary"
                      variant="outlined"
                      size="small"
                    />
                  </Grid>
                ))}
              </Grid>
            )}

            <Divider sx={{ my: 2 }} />
            <Box sx={{ display: "flex", flexWrap: "wrap", gap: 1 }}>
              {Number.isFinite(svc.cold_start_seconds) && (
                <Typography variant="caption" color="text.secondary">
                  Cold start: {svc.cold_start_seconds}s
                </Typography>
              )}
              {Number.isFinite(svc.avg_latency_ms) && (
                <Typography variant="caption" color="text.secondary">
                  Avg latency: {svc.avg_latency_ms}ms
                </Typography>
              )}
              <Typography variant="caption" color="text.secondary">
                Service type: {svc.service_type}
              </Typography>
            </Box>
          </Paper>
        );
      })}
    </Box>
  );
};

export default LocalModelsManagement;
