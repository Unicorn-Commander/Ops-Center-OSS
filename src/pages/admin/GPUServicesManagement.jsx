import React, { useState, useEffect, useCallback } from "react";
import {
  Box, Paper, Typography, Button, Grid, Card, CardContent,
  Alert, CircularProgress, Chip, LinearProgress, Divider,
} from "@mui/material";
import {
  Refresh as RefreshIcon, Memory as GpuIcon,
  CheckCircle as HealthyIcon, Cancel as UnhealthyIcon,
  Computer as ServerIcon, Hub as HubIcon,
  Schedule as ScheduleIcon, Timer as TimerIcon,
} from "@mui/icons-material";
import PageHeader from "../../components/admin/PageHeader";
import { fetchFederationJson, federationTimeAgo } from "../../utils/federationApi";

const API_BASE = "/api/v1/compute";

const GPUServicesManagement = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [nodes, setNodes] = useState([]);
  const [refreshing, setRefreshing] = useState(false);

  const fetchNodes = useCallback(async () => {
    try {
      const data = await fetchFederationJson(`${API_BASE}/nodes`);
      setNodes(data.nodes || []);
      setError(null);
    } catch (err) {
      console.error("Failed to fetch compute nodes:", err);
      setError(err.message);
    }
  }, []);

  useEffect(() => {
    fetchNodes().finally(() => setLoading(false));
  }, [fetchNodes]);

  useEffect(() => {
    const interval = setInterval(fetchNodes, 30000);
    return () => clearInterval(interval);
  }, [fetchNodes]);

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchNodes();
    setRefreshing(false);
  };

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
        title="GPU Compute Fabric"
        subtitle="Federated GPU inventory across all Unicorn nodes"
        actions={
          <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
            <Chip
              icon={nodes.length > 0 ? <HealthyIcon /> : <UnhealthyIcon />}
              label={`${nodes.length} node(s)`}
              color={nodes.length > 0 ? "success" : "default"}
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

      {nodes.length === 0 && (
        <Alert severity="warning" sx={{ mb: 2 }}>
          No federation peers reachable. Check federation settings or agent connectivity.
        </Alert>
      )}

      {nodes.map((node) => {
        const gpus = node.gpu_info || [];
        const totalMem = gpus.reduce((s, g) => s + (g.memory_total_mb || g.memory_total || 0), 0);
        const usedMem = gpus.reduce((s, g) => s + (g.memory_used_mb || g.memory_used || 0), 0);
        const isOnline = node.status === "active" && new Date(node.last_heartbeat).getTime() > Date.now() - 120000;

        return (
          <Paper key={node.node_id} sx={{ p: 3, mb: 3, borderRadius: 2 }}>
            <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 2 }}>
              <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                <ServerIcon sx={{ color: isOnline ? "success.main" : "error.main" }} />
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  {node.hostname || node.node_id}
                </Typography>
                <Chip
                  label={isOnline ? "Online" : "Offline"}
                  size="small"
                  color={isOnline ? "success" : "error"}
                  sx={{ fontWeight: 600 }}
                />
                <Chip
                  label={`ID: ${node.node_id}`}
                  size="small"
                  variant="outlined"
                />
              </Box>
              <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                <ScheduleIcon sx={{ fontSize: 16, color: "text.secondary" }} />
                <Typography variant="caption" color="text.secondary">
                  {node.last_heartbeat
                    ? `Last seen ${federationTimeAgo(node.last_heartbeat)}`
                    : "No heartbeat"}
                </Typography>
              </Box>
            </Box>

            {gpus.length === 0 ? (
              <Alert severity="info" sx={{ my: 1 }}>
                No GPU hardware reported by this node.
              </Alert>
            ) : (
              <Grid container spacing={2}>
                {gpus.map((gpu, idx) => {
                  const used = gpu.memory_used_mb || gpu.memory_used || 0;
                  const total = gpu.memory_total_mb || gpu.memory_total || 1;
                  const pct = Math.min(100, (used / total) * 100);
                  return (
                    <Grid item xs={12} md={6} key={idx}>
                      <Card sx={{ borderRadius: 2, bgcolor: "background.default" }}>
                        <CardContent>
                          <Box sx={{ display: "flex", justifyContent: "space-between", mb: 1 }}>
                            <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                              <GpuIcon sx={{ color: "primary.main", fontSize: 20 }} />
                              <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                                GPU {gpu.index ?? idx}: {gpu.name || "Unknown"}
                              </Typography>
                            </Box>
                            <Chip
                              label={gpu.temperature ? `${gpu.temperature}°C` : "N/A"}
                              size="small"
                              color={gpu.temperature > 80 ? "error" : gpu.temperature > 70 ? "warning" : "default"}
                              variant="outlined"
                            />
                          </Box>
                          <Box sx={{ mb: 1 }}>
                            <Box sx={{ display: "flex", justifyContent: "space-between", mb: 0.5 }}>
                              <Typography variant="caption">VRAM</Typography>
                              <Typography variant="caption">
                                {used.toLocaleString()} / {total.toLocaleString()} MB
                              </Typography>
                            </Box>
                            <LinearProgress
                              variant="determinate"
                              value={pct}
                              sx={{
                                height: 8, borderRadius: 4,
                                backgroundColor: "rgba(0,0,0,0.1)",
                                "& .MuiLinearProgress-bar": {
                                  borderRadius: 4,
                                  backgroundColor: pct > 90 ? "#f44336" : pct > 70 ? "#ff9800" : "#4caf50",
                                },
                              }}
                            />
                            <Box sx={{ display: "flex", justifyContent: "space-between", mt: 0.5 }}>
                              <Typography variant="caption" color="text.secondary">
                                {pct.toFixed(1)}% used
                              </Typography>
                              <Typography variant="caption" color="text.secondary">
                                {(total - used).toLocaleString()} MB free
                              </Typography>
                            </Box>
                          </Box>
                          {gpu.utilization !== undefined && gpu.utilization !== null && (
                            <Typography variant="caption" color="text.secondary">
                              GPU Util: {gpu.utilization}% | Power: {gpu.power_watts ?? "N/A"}W
                            </Typography>
                          )}
                        </CardContent>
                      </Card>
                    </Grid>
                  );
                })}
                <Grid item xs={12}>
                  <Divider sx={{ my: 1 }} />
                  <Box sx={{ display: "flex", justifyContent: "space-between" }}>
                    <Typography variant="body2" color="text.secondary">
                      Total VRAM: {usedMem.toLocaleString()} / {totalMem.toLocaleString()} MB
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {gpus.length} GPU{gpus.length !== 1 ? "s" : ""} • Loaded: {node.loaded_models?.length || 0} model(s)
                    </Typography>
                  </Box>
                </Grid>
              </Grid>
            )}

            {node.capabilities?.length > 0 && (
              <Box sx={{ mt: 2 }}>
                <Typography variant="caption" color="text.secondary" sx={{ mr: 1 }}>
                  Capabilities:
                </Typography>
                {node.capabilities.map((cap) => (
                  <Chip key={cap} label={cap} size="small" sx={{ mr: 0.5, mb: 0.5 }} />
                ))}
              </Box>
            )}
          </Paper>
        );
      })}
    </Box>
  );
};

export default GPUServicesManagement;
