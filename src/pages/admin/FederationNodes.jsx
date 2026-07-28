/**
 * Federation Nodes Management Page
 * Displays all federation nodes with status, hardware, and service details.
 * Auto-refreshes every 30 seconds.
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Table,
  TableHead,
  TableBody,
  TableRow,
  TableCell,
  Chip,
  IconButton,
  Collapse,
  Card,
  CardContent,
  Typography,
  Button,
  Alert,
  CircularProgress,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  Delete as DeleteIcon
} from '@mui/icons-material';
import PageHeader from '../../components/admin/PageHeader';
import { fetchFederationJson, federationTimeAgo } from '../../utils/federationApi';

const STATUS_COLORS = {
  online: 'success',
  degraded: 'warning',
  offline: 'error'
};

const STATUS_ICONS = {
  online: '\u{1F7E2}',
  degraded: '\u{1F7E1}',
  offline: '\u{1F534}'
};

export default function FederationNodes() {
  const [nodes, setNodes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [expandedNode, setExpandedNode] = useState(null);
  const [deregisterTarget, setDeregisterTarget] = useState(null);

  const fetchNodes = useCallback(async () => {
    try {
      const data = await fetchFederationJson('/api/v1/federation/nodes');
      setNodes(data.nodes || []);
      setError('');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchNodes();
    const interval = setInterval(fetchNodes, 30000);
    return () => clearInterval(interval);
  }, [fetchNodes]);

  const handleDeregister = async () => {
    if (!deregisterTarget) return;
    try {
      await fetchFederationJson(`/api/v1/federation/nodes/${deregisterTarget}`, {
        method: 'DELETE'
      });
      setDeregisterTarget(null);
      fetchNodes();
    } catch (err) {
      setError(err.message);
      setDeregisterTarget(null);
    }
  };

  const toggleExpand = (nodeId) => {
    setExpandedNode(prev => (prev === nodeId ? null : nodeId));
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 8 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <PageHeader
        title="Federation Nodes"
        subtitle="Manage nodes in the federation mesh"
        actions={
          <Button startIcon={<RefreshIcon />} onClick={fetchNodes} variant="outlined" size="small">
            Refresh
          </Button>
        }
      />

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {nodes.length === 0 && !error ? (
        <Alert severity="info">No federation nodes registered yet.</Alert>
      ) : (
        <Card>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell />
                <TableCell>Node</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Endpoint</TableCell>
                <TableCell>Hardware</TableCell>
                <TableCell>Services</TableCell>
                <TableCell>Last Heartbeat</TableCell>
                <TableCell>Region</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {nodes.map((node) => {
                const isExpanded = expandedNode === node.node_id;
                const gpuCount = node.hardware?.gpus?.length || node.hardware?.gpu_count || 0;
                const ramGb = node.hardware?.ram_gb || node.hardware?.total_ram_gb || '?';
                const servicesCount = node.services?.length || 0;

                return (
                  <React.Fragment key={node.node_id}>
                    <TableRow
                      hover
                      sx={{ cursor: 'pointer', '& > *': { borderBottom: isExpanded ? 'none' : undefined } }}
                      onClick={() => toggleExpand(node.node_id)}
                    >
                      <TableCell sx={{ width: 40 }}>
                        <IconButton size="small">
                          {isExpanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                        </IconButton>
                      </TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          {node.branding?.logo && (
                            <Box
                              component="img"
                              src={node.branding.logo}
                              alt=""
                              sx={{ width: 24, height: 24, borderRadius: 1 }}
                            />
                          )}
                          <Box>
                            <Typography variant="body2" fontWeight={600}>
                              {node.display_name || node.node_id}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              {node.node_id}
                            </Typography>
                          </Box>
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={`${STATUS_ICONS[node.status] || ''} ${node.status}`}
                          color={STATUS_COLORS[node.status] || 'default'}
                          size="small"
                          variant="outlined"
                        />
                      </TableCell>
                      <TableCell>
                        <Typography variant="caption" sx={{ fontFamily: 'monospace' }}>
                          {node.endpoint_url}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {gpuCount} GPU{gpuCount !== 1 ? 's' : ''}, {ramGb} GB RAM
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip label={servicesCount} size="small" />
                      </TableCell>
                      <TableCell>
                        <Tooltip title={node.last_heartbeat || 'Never'}>
                          <Typography variant="body2">{federationTimeAgo(node.last_heartbeat)}</Typography>
                        </Tooltip>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">{node.region || '-'}</Typography>
                      </TableCell>
                      <TableCell align="right">
                        <Tooltip title="Deregister node">
                          <IconButton
                            size="small"
                            color="error"
                            onClick={(e) => {
                              e.stopPropagation();
                              setDeregisterTarget(node.node_id);
                            }}
                          >
                            <DeleteIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      </TableCell>
                    </TableRow>

                    <TableRow>
                      <TableCell colSpan={9} sx={{ py: 0, px: 0 }}>
                        <Collapse in={isExpanded} timeout="auto" unmountOnExit>
                          <Box sx={{ p: 2, bgcolor: 'action.hover' }}>
                            <Typography variant="subtitle2" gutterBottom>
                              Hardware Profile
                            </Typography>
                            {node.hardware ? (
                              <Box sx={{ mb: 2 }}>
                                <Typography variant="body2">
                                  CPU: {node.hardware.cpu || 'Unknown'} | RAM: {ramGb} GB
                                </Typography>
                                {node.hardware.gpus?.map((gpu, idx) => (
                                  <Typography key={idx} variant="body2">
                                    GPU {idx}: {gpu.name || gpu.model || 'Unknown'} ({gpu.vram_gb || gpu.memory_gb || '?'} GB)
                                  </Typography>
                                ))}
                              </Box>
                            ) : (
                              <Typography variant="body2" color="text.secondary">
                                No hardware information available
                              </Typography>
                            )}

                            <Typography variant="subtitle2" gutterBottom>
                              Services ({servicesCount})
                            </Typography>
                            {node.services?.length > 0 ? (
                              <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                                {node.services.map((svc, idx) => (
                                  <Chip
                                    key={idx}
                                    label={`${svc.service_type || svc.type}: ${svc.status || 'unknown'}`}
                                    size="small"
                                    variant="outlined"
                                  />
                                ))}
                              </Box>
                            ) : (
                              <Typography variant="body2" color="text.secondary">
                                No services registered
                              </Typography>
                            )}

                            {node.capabilities && (
                              <Box sx={{ mt: 2 }}>
                                <Typography variant="subtitle2" gutterBottom>
                                  Capabilities
                                </Typography>
                                <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                                  {(Array.isArray(node.capabilities)
                                    ? node.capabilities
                                    : Object.keys(node.capabilities)
                                  ).map((cap, idx) => (
                                    <Chip key={idx} label={cap} size="small" color="primary" variant="outlined" />
                                  ))}
                                </Box>
                              </Box>
                            )}
                          </Box>
                        </Collapse>
                      </TableCell>
                    </TableRow>
                  </React.Fragment>
                );
              })}
            </TableBody>
          </Table>
        </Card>
      )}

      {/* Deregister Confirmation Dialog */}
      <Dialog open={!!deregisterTarget} onClose={() => setDeregisterTarget(null)}>
        <DialogTitle>Deregister Node</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to deregister node <strong>{deregisterTarget}</strong>? This will remove it from the federation mesh.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeregisterTarget(null)}>Cancel</Button>
          <Button onClick={handleDeregister} color="error" variant="contained">
            Deregister
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
