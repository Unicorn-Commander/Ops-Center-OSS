/**
 * Federation Service Catalog
 * Outbound = what this Ops-Center advertises to peers.
 * Inbound = what peers advertise back into the federation catalog.
 */

import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Divider,
  FormControl,
  Grid,
  InputLabel,
  MenuItem,
  Select,
  Stack,
  Typography,
} from '@mui/material';
import { Refresh as RefreshIcon } from '@mui/icons-material';
import PageHeader from '../../components/admin/PageHeader';
import {
  endpointWithPath,
  fetchFederationJson,
  federationTimeAgo,
  getEndpointHost,
} from '../../utils/federationApi';

const SERVICE_TYPES = [
  { value: 'all', label: 'All Types' },
  { value: 'llm', label: 'LLM' },
  { value: 'tts', label: 'TTS' },
  { value: 'stt', label: 'STT' },
  { value: 'embeddings', label: 'Embeddings' },
  { value: 'image_gen', label: 'Image Generation' },
  { value: 'music_gen', label: 'Music Generation' },
  { value: 'reranker', label: 'Reranker' },
  { value: 'agents', label: 'Agents' },
  { value: 'search', label: 'Search' },
  { value: 'extraction', label: 'Extraction' },
];

const STATUS_COLORS = {
  running: 'success',
  online: 'success',
  healthy: 'success',
  loaded: 'success',
  idle: 'success',
  degraded: 'warning',
  offline: 'error',
  failed: 'error',
  unknown: 'default',
};

function statusColor(status) {
  return STATUS_COLORS[(status || 'unknown').toLowerCase()] || 'default';
}

function statusBorderColor(status) {
  const color = statusColor(status);
  if (color === 'success') return 'success.main';
  if (color === 'warning') return 'warning.main';
  if (color === 'error') return 'error.main';
  return 'divider';
}

function parseJsonField(value, fallback) {
  if (typeof value !== 'string') return value ?? fallback;
  try {
    return JSON.parse(value);
  } catch (_error) {
    return fallback;
  }
}

function normalizeService(service) {
  return {
    ...service,
    capabilities: parseJsonField(service.capabilities, {}),
    models: parseJsonField(service.models, []),
  };
}

function capabilityChips(capabilities) {
  capabilities = parseJsonField(capabilities, {});
  if (!capabilities) return [];
  if (Array.isArray(capabilities)) return capabilities.map(String);

  return Object.entries(capabilities)
    .flatMap(([key, value]) => {
      if (value === false || value == null) return [];
      if (value === true) return [key];
      if (Array.isArray(value)) return [`${key}:${value.join(',')}`];
      return [`${key}:${value}`];
    })
    .slice(0, 8);
}

function ServiceRow({ service, fallbackEndpoint, fallbackStatus, fallbackLastSeen }) {
  service = normalizeService(service);
  const endpoint = endpointWithPath(fallbackEndpoint, service.endpoint_path);
  const health = service.node_status || service.status || fallbackStatus || 'unknown';
  const capabilities = capabilityChips(service.capabilities);
  const lastSeen = service.last_heartbeat || fallbackLastSeen;
  const models = Array.isArray(service.models) ? service.models : [];

  return (
    <Box sx={{ py: 1.5 }}>
      <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap" useFlexGap sx={{ mb: 1 }}>
        <Chip
          label={(service.service_type || 'unknown').toUpperCase().replace('_', ' ')}
          size="small"
          color="primary"
          variant="outlined"
        />
        <Chip
          label={health}
          size="small"
          color={statusColor(health)}
          variant="outlined"
        />
      </Stack>

      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', fontFamily: 'monospace', mb: 1 }}>
        {endpoint}
      </Typography>

      <Stack direction="row" spacing={2} flexWrap="wrap" useFlexGap sx={{ mb: capabilities.length || service.models?.length ? 1 : 0 }}>
        <Typography variant="caption" color="text.secondary">
          Last seen: {lastSeen ? federationTimeAgo(lastSeen) : 'Local snapshot'}
        </Typography>
        {service.avg_latency_ms != null && (
          <Typography variant="caption" color="text.secondary">
            Latency: {service.avg_latency_ms}ms
          </Typography>
        )}
        {service.cold_start_seconds != null && (
          <Typography variant="caption" color="text.secondary">
            Cold start: {service.cold_start_seconds}s
          </Typography>
        )}
      </Stack>

      {capabilities.length > 0 && (
        <Stack direction="row" spacing={0.75} flexWrap="wrap" useFlexGap sx={{ mb: service.models?.length ? 1 : 0 }}>
          {capabilities.map((entry) => (
            <Chip key={entry} label={entry} size="small" variant="outlined" sx={{ fontSize: '0.72rem' }} />
          ))}
        </Stack>
      )}

      {models.length > 0 && (
        <Stack direction="row" spacing={0.75} flexWrap="wrap" useFlexGap>
          {models.slice(0, 6).map((model) => (
            <Chip key={model} label={model} size="small" variant="outlined" sx={{ fontSize: '0.72rem' }} />
          ))}
          {models.length > 6 && (
            <Chip label={`+${models.length - 6} more`} size="small" variant="outlined" sx={{ fontSize: '0.72rem' }} />
          )}
        </Stack>
      )}
    </Box>
  );
}

export default function FederationServiceCatalog() {
  const [services, setServices] = useState([]);
  const [topology, setTopology] = useState({ nodes: [] });
  const [advertisement, setAdvertisement] = useState({ services: [], hardware_profile: {} });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [filter, setFilter] = useState('all');

  const fetchCatalog = useCallback(async () => {
    try {
      const [servicesData, topologyData, advertisementData] = await Promise.all([
        fetchFederationJson('/api/v1/federation/services'),
        fetchFederationJson('/api/v1/federation/topology'),
        fetchFederationJson('/api/v1/federation/self/advertisement'),
      ]);

      setServices((servicesData.services || []).map(normalizeService));
      setTopology({ nodes: topologyData.nodes || [] });
      setAdvertisement({
        services: advertisementData.services || [],
        hardware_profile: advertisementData.hardware_profile || {},
      });
      setError('');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchCatalog();
    const interval = setInterval(fetchCatalog, 30000);
    return () => clearInterval(interval);
  }, [fetchCatalog]);

  const filteredServices = useMemo(() => {
    if (filter === 'all') return services;
    return services.filter((service) => service.service_type === filter);
  }, [filter, services]);

  const nodeLookup = useMemo(() => {
    return new Map((topology.nodes || []).map((node) => [node.node_id, node]));
  }, [topology.nodes]);

  const currentHost = typeof window !== 'undefined' ? window.location.hostname.toLowerCase() : '';

  const localNode = useMemo(() => {
    return (topology.nodes || []).find((node) => {
      const host = getEndpointHost(node.endpoint_url || '', '').toLowerCase();
      return host && (host === currentHost || host.endsWith(currentHost) || currentHost.endsWith(host));
    }) || null;
  }, [currentHost, topology.nodes]);

  const outboundServicesRaw = useMemo(() => {
    const localEndpoint = localNode?.endpoint_url || (typeof window !== 'undefined' ? window.location.origin : '');
    return (advertisement.services || []).map((service) => ({
      ...service,
      node_status: localNode?.status || service.status || 'running',
      last_heartbeat: localNode?.last_heartbeat || null,
      endpoint_url: localEndpoint,
    }));
  }, [advertisement.services, localNode]);

  const outboundServices = useMemo(() => {
    if (filter === 'all') return outboundServicesRaw;
    return outboundServicesRaw.filter((service) => service.service_type === filter);
  }, [filter, outboundServicesRaw]);

  const inboundPeers = useMemo(() => {
    const grouped = new Map();

    filteredServices.forEach((service) => {
      if (localNode && service.node_id === localNode.node_id) {
        return;
      }

      const node = nodeLookup.get(service.node_id) || {};
      const host = getEndpointHost(node.endpoint_url || service.endpoint_url || '', service.node_id);
      const existing = grouped.get(service.node_id) || {
        node_id: service.node_id,
        display_name: node.display_name || service.display_name || service.node_id,
        endpoint_url: node.endpoint_url || service.endpoint_url || '',
        host,
        status: node.status || service.node_status || service.status || 'unknown',
        last_heartbeat: node.last_heartbeat || service.last_heartbeat || null,
        services: [],
      };

      existing.services.push({
        ...service,
        last_heartbeat: service.last_heartbeat || existing.last_heartbeat,
      });
      grouped.set(service.node_id, existing);
    });

    return Array.from(grouped.values()).sort((left, right) => {
      const leftName = `${left.display_name} ${left.host}`.toLowerCase();
      const rightName = `${right.display_name} ${right.host}`.toLowerCase();
      return leftName.localeCompare(rightName);
    });
  }, [filteredServices, localNode, nodeLookup]);

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
        title="Federation Service Catalog"
        subtitle="Outbound self-advertisement alongside inbound peer service inventory"
        actions={(
          <Button startIcon={<RefreshIcon />} onClick={fetchCatalog} variant="outlined" size="small">
            Refresh
          </Button>
        )}
      />

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap" sx={{ mb: 3 }}>
        <Chip label={`${outboundServices.length} outbound service${outboundServices.length === 1 ? '' : 's'}`} color="primary" variant="outlined" />
        <Chip label={`${inboundPeers.length} peer${inboundPeers.length === 1 ? '' : 's'}`} color="success" variant="outlined" />
        <Chip label={`${filteredServices.length} inbound service${filteredServices.length === 1 ? '' : 's'}`} variant="outlined" />
      </Stack>

      <Box sx={{ mb: 3 }}>
        <FormControl size="small" sx={{ minWidth: 220 }}>
          <InputLabel id="federation-service-filter">Service Type</InputLabel>
          <Select
            labelId="federation-service-filter"
            value={filter}
            label="Service Type"
            onChange={(event) => setFilter(event.target.value)}
          >
            {SERVICE_TYPES.map((option) => (
              <MenuItem key={option.value} value={option.value}>
                {option.label}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
      </Box>

      <Grid container spacing={3}>
        <Grid item xs={12} lg={5}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Typography variant="h6" fontWeight={600} gutterBottom>
                Outbound
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                What this Ops-Center instance publishes for peers to consume.
              </Typography>

              <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap" sx={{ mb: 2 }}>
                <Chip
                  label={localNode?.status || 'local snapshot'}
                  size="small"
                  color={statusColor(localNode?.status || 'running')}
                  variant="outlined"
                />
                <Chip
                  label={localNode?.last_heartbeat ? `Last seen ${federationTimeAgo(localNode.last_heartbeat)}` : 'Derived from /self/advertisement'}
                  size="small"
                  variant="outlined"
                />
              </Stack>

              {outboundServices.length === 0 ? (
                <Alert severity="info">No outbound services are advertised right now.</Alert>
              ) : (
                outboundServices.map((service, index) => (
                  <React.Fragment key={`outbound-${service.service_type}-${index}`}>
                    {index > 0 && <Divider />}
                    <ServiceRow
                      service={service}
                      fallbackEndpoint={service.endpoint_url}
                      fallbackStatus={service.node_status}
                      fallbackLastSeen={service.last_heartbeat}
                    />
                  </React.Fragment>
                ))
              )}
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} lg={7}>
          <Card sx={{ mb: 2 }}>
            <CardContent>
              <Typography variant="h6" fontWeight={600} gutterBottom>
                Inbound
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Peer services grouped by the hostname they advertise into this federation catalog.
              </Typography>
            </CardContent>
          </Card>

          {inboundPeers.length === 0 ? (
            <Alert severity="info">No peer services matched the current filter.</Alert>
          ) : (
            <Grid container spacing={2}>
              {inboundPeers.map((peer) => (
                <Grid item xs={12} key={peer.node_id}>
                  <Card sx={{ borderLeft: 3, borderColor: statusBorderColor(peer.status) }}>
                    <CardContent>
                      <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap" useFlexGap sx={{ mb: 1 }}>
                        <Typography variant="subtitle1" fontWeight={600}>
                          {peer.display_name}
                        </Typography>
                        <Chip label={peer.host} size="small" variant="outlined" />
                        <Chip label={peer.status} size="small" color={statusColor(peer.status)} variant="outlined" />
                      </Stack>

                      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', fontFamily: 'monospace', mb: 1 }}>
                        {peer.endpoint_url || peer.host}
                      </Typography>

                      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1.5 }}>
                        Last seen: {peer.last_heartbeat ? federationTimeAgo(peer.last_heartbeat) : 'Unknown'}
                      </Typography>

                      {peer.services.map((service, index) => (
                        <React.Fragment key={`${peer.node_id}-${service.service_type}-${index}`}>
                          {index > 0 && <Divider />}
                          <ServiceRow
                            service={service}
                            fallbackEndpoint={peer.endpoint_url}
                            fallbackStatus={peer.status}
                            fallbackLastSeen={peer.last_heartbeat}
                          />
                        </React.Fragment>
                      ))}
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
          )}
        </Grid>
      </Grid>
    </Box>
  );
}
