// CloudflareDNS constants - Record types and TTL options

export const RECORD_TYPES = ['A', 'AAAA', 'CNAME', 'MX', 'TXT', 'NS', 'SRV', 'CAA'];

export const TTL_OPTIONS = [
  { value: 1, label: 'Auto' },
  { value: 60, label: '1 minute' },
  { value: 300, label: '5 minutes' },
  { value: 600, label: '10 minutes' },
  { value: 3600, label: '1 hour' },
  { value: 86400, label: '1 day' }
];

export const ZONE_PRIORITIES = [
  { value: 'critical', label: 'Critical - Add First' },
  { value: 'high', label: 'High Priority' },
  { value: 'normal', label: 'Normal Priority' },
  { value: 'low', label: 'Low Priority' }
];
