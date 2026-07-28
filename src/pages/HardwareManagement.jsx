import React, { useState, useEffect, useCallback, useMemo } from "react";
import {
  Box, Grid, Paper, Typography, LinearProgress, CircularProgress,
  Card, CardContent, Chip, Alert, AlertTitle, IconButton, Tooltip,
  Button, Divider, ToggleButtonGroup, ToggleButton,
} from "@mui/material";
import {
  Memory as MemoryIcon, Computer as ComputerIcon,
  Storage as StorageIcon, Speed as SpeedIcon,
  Refresh as RefreshIcon, Warning as WarningIcon,
  CheckCircle as CheckIcon, Error as ErrorIcon,
  Dns as NodeIcon, Hub as HubIcon,
} from "@mui/icons-material";
import {
  LineChart, Line, AreaChart, Area, XAxis, YAxis,
  CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer,
} from "recharts";
import { fetchFederationJson, federationTimeAgo } from "../utils/federationApi";
import { safeToFixed } from "../utils/safeNumberUtils";

const HardwareManagement = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [nodes, setNodes] = useState([]);
  const [topology, setTopology] = useState(null);
  const [refreshing, setRefreshing] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [viewMode, setViewMode] = useState("nodes");

  const fetchData = useCallback(async () => {
    try {
      const [nodesResp, topoResp] = await Promise.all([
        fetchFederationJson("/api/v1/compute/nodes"),
        fetchFederationJson("/api/v1/federation/topology"),
      ]);
      setNodes(nodesResp.nodes || []);
      setTopology(topoResp);
      setError(null);
    } catch (err) {
      console.error("Failed to fetch hardware data:", err);
      setError(err.message);
    }
  }, []);

  useEffect(() => {
    fetchData().finally(() => setLoading(false));
  }, [fetchData]);

  useEffect(() => {
    if (!autoRefresh) return;
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, [autoRefresh, fetchData]);

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchData();
    setRefreshing(false);
  };

  const formatGB = (mb) => {
    if (!mb) return "0";
    return safeToFixed(mb / 1024, 1);
  };

  const onlineNodes = useMemo(
    () => nodes.filter((n) => n.status === "active" || n.is_online),
    [nodes]
  );

  const allGpus = useMemo(
    () =>
      nodes.flatMap((n) =>
        (n.gpu_info || []).map((g) => ({ ...g, node_id: n.node_id, hostname: n.hostname }))
      ),
    [nodes]
  );

  const totalVramMb = allGpus.reduce((s, g) => s + (g.memory_total_mb || g.memory_total || 0), 0);
  const usedVramMb = allGpus.reduce((s, g) => s + (g.memory_used_mb || g.memory_used || 0), 0);

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box>
          <Typography variant="h4" fontWeight="bold">Hardware Management</Typography>
          <Typography variant="body2" color="text.secondary" mt={0.5}>
            Federated hardware inventory across {nodes.length} node{nodes.length !== 1 ? "s" : ""}
            {" "}({onlineNodes.length} online, {topology?.service_count || 0} services)
          </Typography>
        </Box>
        <Box display="flex" gap={2} alignItems="center">
          <Chip
            label={autoRefresh ? "Auto-refresh: 30s" : "Auto-refresh: OFF"}
            color={autoRefresh ? "success" : "default"}
            onClick={() => setAutoRefresh(!autoRefresh)}
            sx={{ cursor: "pointer" }}
          />
          <Tooltip title="Refresh All">
            <IconButton onClick={handleRefresh} disabled={refreshing} color="primary">
              <RefreshIcon sx={{ animation: refreshing ? "spin 1s linear infinite" : "none" }} />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} action={
          <Button color="inherit" size="small" onClick={handleRefresh}>Retry</Button>
        }>
          <AlertTitle>Failed to Load</AlertTitle>
          {error}
        </Alert>
      )}

      {nodes.length === 0 && (
        <Alert severity="warning" sx={{ mb: 3 }}>
          <AlertTitle>No Federation Peers Reachable</AlertTitle>
          No nodes are reporting to the federation compute fabric. Check that GPU agents
          are running on your GPU nodes and that the federation mesh is healthy.
        </Alert>
      )}

      {/* Fleet Summary */}
      <Grid container spacing={3} mb={3}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" mb={1}>
                <NodeIcon sx={{ mr: 1, color: "primary.main" }} />
                <Typography variant="h6">Nodes</Typography>
              </Box>
              <Typography variant="h3" fontWeight="bold">
                {nodes.length}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {onlineNodes.length} online
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" mb={1}>
                <SpeedIcon sx={{ mr: 1, color: "success.main" }} />
                <Typography variant="h6">GPUs</Typography>
              </Box>
              <Typography variant="h3" fontWeight="bold">
                {allGpus.length}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {nodes.length} host{nodes.length !== 1 ? "s" : ""}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" mb={1}>
                <MemoryIcon sx={{ mr: 1, color: "warning.main" }} />
                <Typography variant="h6">Total VRAM</Typography>
              </Box>
              <Typography variant="h3" fontWeight="bold">
                {formatGB(totalVramMb)} GB
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {formatGB(usedVramMb)} GB used ({totalVramMb > 0 ? safeToFixed((usedVramMb / totalVramMb) * 100, 1) : 0}%)
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" mb={1}>
                <HubIcon sx={{ mr: 1, color: "info.main" }} />
                <Typography variant="h6">Services</Typography>
              </Box>
              <Typography variant="h3" fontWeight="bold">
                {topology?.service_count || 0}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {topology?.online_nodes || 0} online nodes
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Per-node hardware cards */}
      <ToggleButtonGroup
        value={viewMode}
        exclusive
        onChange={(e, v) => v && setViewMode(v)}
        size="small"
        sx={{ mb: 3 }}
      >
        <ToggleButton value="nodes">Node View</ToggleButton>
        <ToggleButton value="gpus">GPU Grid</ToggleButton>
        <ToggleButton value="topology">Topology</ToggleButton>
      </ToggleButtonGroup>

      {viewMode === "nodes" && nodes.map((node) => {
        const gpus = node.gpu_info || [];
        const isOnline = node.status === "active" && node.last_heartbeat &&
          new Date(node.last_heartbeat).getTime() > Date.now() - 120000;
        const nodeVram = gpus.reduce((s, g) => s + (g.memory_total_mb || g.memory_total || 0), 0);
        const nodeUsed = gpus.reduce((s, g) => s + (g.memory_used_mb || g.memory_used || 0), 0);

        return (
          <Paper key={node.node_id} sx={{ p: 3, mb: 3, borderRadius: 2 }}>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Box display="flex" alignItems="center" gap={1}>
                <NodeIcon sx={{ color: isOnline ? "success.main" : "error.main" }} />
                <Typography variant="h6" fontWeight={600}>
                  {node.hostname || node.node_id}
                </Typography>
                <Chip
                  label={isOnline ? "Online" : "Offline"}
                  size="small"
                  color={isOnline ? "success" : "error"}
                />
              </Box>
              <Typography variant="caption" color="text.secondary">
                {node.last_heartbeat
                  ? `Last heartbeat: ${federationTimeAgo(node.last_heartbeat)}`
                  : "Never"}
              </Typography>
            </Box>

            {gpus.length > 0 ? (
              <Grid container spacing={2}>
                {gpus.map((gpu, idx) => {
                  const used = gpu.memory_used_mb || gpu.memory_used || 0;
                  const total = gpu.memory_total_mb || gpu.memory_total || 1;
                  const pct = (used / total) * 100;
                  return (
                    <Grid item xs={12} md={6} lg={4} key={idx}>
                      <Card sx={{ borderRadius: 2, bgcolor: "background.default" }}>
                        <CardContent>
                          <Typography variant="subtitle2" fontWeight={600} noWrap>
                            GPU {gpu.index ?? idx}: {gpu.name || "Unknown"}
                          </Typography>
                          <Box mt={1}>
                            <Box display="flex" justifyContent="space-between">
                              <Typography variant="caption">VRAM</Typography>
                              <Typography variant="caption">
                                {used.toLocaleString()} / {total.toLocaleString()} MB
                              </Typography>
                            </Box>
                            <LinearProgress
                              variant="determinate"
                              value={Math.min(100, pct)}
                              sx={{ height: 6, borderRadius: 3, my: 0.5 }}
                            />
                          </Box>
                          {gpu.temperature != null && (
                            <Chip
                              label={`${gpu.temperature}°C`}
                              size="small"
                              color={gpu.temperature > 80 ? "error" : gpu.temperature > 70 ? "warning" : "success"}
                              sx={{ mt: 0.5 }}
                            />
                          )}
                        </CardContent>
                      </Card>
                    </Grid>
                  );
                })}
                <Grid item xs={12}>
                  <Divider sx={{ my: 1 }} />
                  <Box display="flex" justifyContent="space-between">
                    <Typography variant="body2" color="text.secondary">
                      Total: {formatGB(nodeVram)} GB ({formatGB(nodeUsed)} GB used)
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Models loaded: {node.loaded_models?.length || 0}
                    </Typography>
                  </Box>
                </Grid>
              </Grid>
            ) : (
              <Alert severity="info">No GPU hardware info reported.</Alert>
            )}

            {node.capabilities?.length > 0 && (
              <Box mt={2}>
                <Typography variant="caption" color="text.secondary" mr={1}>
                  Capabilities:
                </Typography>
                {node.capabilities.map((c) => (
                  <Chip key={c} label={c} size="small" sx={{ mr: 0.5, mb: 0.5 }} />
                ))}
              </Box>
            )}
          </Paper>
        );
      })}

      {viewMode === "gpus" && (
        <Grid container spacing={2}>
          {allGpus.length === 0 ? (
            <Grid item xs={12}>
              <Alert severity="info">No GPUs found across federation.</Alert>
            </Grid>
          ) : (
            allGpus.map((gpu, idx) => {
              const used = gpu.memory_used_mb || gpu.memory_used || 0;
              const total = gpu.memory_total_mb || gpu.memory_total || 1;
              const pct = (used / total) * 100;
              return (
                <Grid item xs={12} sm={6} md={4} key={idx}>
                  <Card sx={{ borderRadius: 2 }}>
                    <CardContent>
                      <Box display="flex" justifyContent="space-between" alignItems="start">
                        <Typography variant="subtitle2" fontWeight={600} noWrap>
                          {gpu.name || "Unknown GPU"}
                        </Typography>
                        <Chip label={gpu.hostname || gpu.node_id} size="small" variant="outlined" />
                      </Box>
                      <Box mt={1.5}>
                        <Box display="flex" justifyContent="space-between">
                          <Typography variant="caption">VRAM</Typography>
                          <Typography variant="caption">
                            {used.toLocaleString()} / {total.toLocaleString()} MB
                          </Typography>
                        </Box>
                        <LinearProgress
                          variant="determinate"
                          value={Math.min(100, pct)}
                          sx={{ height: 6, borderRadius: 3, my: 0.5 }}
                        />
                      </Box>
                      <Typography variant="caption" color="text.secondary">
                        {safeToFixed(pct, 1)}% used
                        {gpu.temperature != null ? ` • ${gpu.temperature}°C` : ""}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              );
            })
          )}
        </Grid>
      )}

      {viewMode === "topology" && (
        <Paper sx={{ p: 3, borderRadius: 2 }}>
          <Typography variant="h6" fontWeight={600} mb={2}>
            Federation Topology
          </Typography>
          <Typography variant="body2" color="text.secondary" mb={2}>
            {topology?.online_nodes || 0} online / {topology?.nodes?.length || 0} total nodes
            {" "}• {topology?.service_count || 0} services
          </Typography>
          {topology?.nodes?.length > 0 ? (
            topology.nodes.map((node) => {
              const isOnline = node.status === "online";
              return (
                <Card key={node.node_id} sx={{ mb: 1.5, borderRadius: 2 }}>
                  <CardContent sx={{ py: 1.5, "&:last-child": { pb: 1.5 } }}>
                    <Box display="flex" justifyContent="space-between" alignItems="center">
                      <Box display="flex" alignItems="center" gap={1}>
                        <NodeIcon sx={{ color: isOnline ? "success.main" : "error.main", fontSize: 20 }} />
                        <Typography variant="body2" fontWeight={600}>
                          {node.display_name || node.node_id}
                        </Typography>
                        <Chip
                          label={isOnline ? "online" : "offline"}
                          size="small"
                          color={isOnline ? "success" : "error"}
                        />
                      </Box>
                      <Typography variant="caption" color="text.secondary">
                        {node.endpoint_url || ""}
                      </Typography>
                    </Box>
                    {node.hardware_profile && Object.keys(node.hardware_profile).length > 0 && (
                      <Box mt={0.5}>
                        <Typography variant="caption" color="text.secondary">
                          GPU: {node.hardware_profile.gpu_model || "N/A"}
                          {" "}• CPU: {node.hardware_profile.cpu_model || "N/A"}
                          {" "}• RAM: {node.hardware_profile.ram_gb || "N/A"} GB
                        </Typography>
                      </Box>
                    )}
                  </CardContent>
                </Card>
              );
            })
          ) : (
            <Alert severity="info">No topology data available.</Alert>
          )}
        </Paper>
      )}
    </Box>
  );
};

export default HardwareManagement;
