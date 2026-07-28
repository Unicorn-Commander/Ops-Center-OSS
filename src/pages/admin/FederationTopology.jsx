/**
 * Federation Topology Page
 * Visual card-based view of federation nodes and their connections.
 * Shows health summary and node status with branding support.
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Card,
  CardContent,
  Chip,
  Typography,
  Button,
  Alert,
  CircularProgress,
  Grid
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  Circle as CircleIcon
} from '@mui/icons-material';
import PageHeader from '../../components/admin/PageHeader';
import { fetchFederationJson } from '../../utils/federationApi';

const STATUS_BORDER = {
  online: '#4caf50',
  degraded: '#ff9800',
  offline: '#f44336'
};

export default function FederationTopology() {
  const [topology, setTopology] = useState({ nodes: [], service_count: 0, online_nodes: 0, total_gpus: 0 });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchTopology = useCallback(async () => {
    try {
      const data = await fetchFederationJson('/api/v1/federation/topology');
      setTopology({
        nodes: data.nodes || [],
        service_count: data.service_count || 0,
        online_nodes: data.online_nodes || 0,
        total_gpus: data.total_gpus || 0
      });
      setError('');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchTopology();
    const interval = setInterval(fetchTopology, 30000);
    return () => clearInterval(interval);
  }, [fetchTopology]);

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 8 }}>
        <CircularProgress />
      </Box>
    );
  }

  const onlineCount = topology.online_nodes;
  const totalNodes = topology.nodes.length;
  const serviceCount = topology.service_count;
  const totalGpus = topology.total_gpus;

  return (
    <Box>
      <PageHeader
        title="Federation Topology"
        subtitle="Visual overview of the federation mesh and node connections"
        actions={
          <Button startIcon={<RefreshIcon />} onClick={fetchTopology} variant="outlined" size="small">
            Refresh
          </Button>
        }
      />

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {/* Health Summary */}
      <Box sx={{ display: 'flex', gap: 2, mb: 3, flexWrap: 'wrap' }}>
        <Chip
          icon={<CircleIcon sx={{ fontSize: 12, color: '#4caf50' }} />}
          label={`${onlineCount} node${onlineCount !== 1 ? 's' : ''} online`}
          color="success"
          variant="outlined"
        />
        <Chip
          label={`${serviceCount} service${serviceCount !== 1 ? 's' : ''} available`}
          color="primary"
          variant="outlined"
        />
        <Chip
          label={`${totalGpus} total GPU${totalGpus !== 1 ? 's' : ''}`}
          variant="outlined"
        />
        <Chip
          label={`${totalNodes} total node${totalNodes !== 1 ? 's' : ''}`}
          variant="outlined"
        />
      </Box>

      {totalNodes === 0 && !error ? (
        <Alert severity="info">No nodes in the federation topology yet.</Alert>
      ) : (
        <Grid container spacing={2}>
          {topology.nodes.map((node) => {
            const borderColor = STATUS_BORDER[node.status] || '#9e9e9e';
            const accentColor = node.branding?.accent_color || borderColor;
            const gpuCount = node.hardware?.gpus?.length || node.hardware?.gpu_count || 0;
            const servicesCount = node.services?.length || 0;

            return (
              <Grid item xs={12} sm={6} md={4} key={node.node_id}>
                <Card
                  sx={{
                    height: '100%',
                    borderLeft: `4px solid ${accentColor}`,
                    transition: 'box-shadow 0.2s',
                    '&:hover': { boxShadow: 4 }
                  }}
                >
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                      {node.branding?.logo && (
                        <Box
                          component="img"
                          src={node.branding.logo}
                          alt=""
                          sx={{ width: 28, height: 28, borderRadius: 1 }}
                        />
                      )}
                      <Typography variant="h6" sx={{ fontWeight: 600, flex: 1 }}>
                        {node.display_name || node.node_id}
                      </Typography>
                      <Chip
                        label={node.status}
                        size="small"
                        sx={{
                          bgcolor: `${borderColor}20`,
                          color: borderColor,
                          fontWeight: 600,
                          borderColor: borderColor,
                          border: '1px solid'
                        }}
                      />
                    </Box>

                    <Typography variant="caption" color="text.secondary" sx={{ fontFamily: 'monospace', display: 'block', mb: 1.5 }}>
                      {node.node_id}
                    </Typography>

                    <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 1 }}>
                      <Chip label={`${gpuCount} GPU${gpuCount !== 1 ? 's' : ''}`} size="small" variant="outlined" />
                      <Chip label={`${servicesCount} service${servicesCount !== 1 ? 's' : ''}`} size="small" variant="outlined" />
                      {node.region && <Chip label={node.region} size="small" variant="outlined" />}
                    </Box>

                    {node.hardware?.gpus?.length > 0 && (
                      <Box sx={{ mt: 1 }}>
                        {node.hardware.gpus.map((gpu, idx) => (
                          <Typography key={idx} variant="caption" color="text.secondary" display="block">
                            {gpu.name || gpu.model || `GPU ${idx}`} ({gpu.vram_gb || gpu.memory_gb || '?'} GB)
                          </Typography>
                        ))}
                      </Box>
                    )}

                    {/* Peer connections */}
                    {node.peers?.length > 0 && (
                      <Box sx={{ mt: 1.5, pt: 1, borderTop: '1px solid', borderColor: 'divider' }}>
                        <Typography variant="caption" color="text.secondary" fontWeight={600}>
                          Connected peers:
                        </Typography>
                        <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap', mt: 0.5 }}>
                          {node.peers.map((peer, idx) => (
                            <Chip key={idx} label={peer} size="small" variant="outlined" sx={{ fontSize: '0.7rem' }} />
                          ))}
                        </Box>
                      </Box>
                    )}
                  </CardContent>
                </Card>
              </Grid>
            );
          })}
        </Grid>
      )}
    </Box>
  );
}
