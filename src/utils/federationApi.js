export async function fetchFederationJson(path, options = {}) {
  const headers = new Headers(options.headers || {});
  const token = localStorage.getItem('authToken');

  if (token && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  const response = await fetch(path, {
    credentials: 'include',
    ...options,
    headers,
  });

  const contentType = response.headers.get('content-type') || '';
  const isJson = contentType.includes('application/json');
  const payload = isJson ? await response.json() : await response.text();

  if (!response.ok) {
    const detail =
      typeof payload === 'string'
        ? payload
        : payload?.detail || payload?.message || payload?.error;
    throw new Error(detail || `Request failed (${response.status})`);
  }

  return payload;
}

export function federationTimeAgo(dateStr) {
  if (!dateStr) return 'Unknown';

  const seconds = Math.floor((Date.now() - new Date(dateStr).getTime()) / 1000);
  if (seconds < 60) return `${seconds}s ago`;

  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;

  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;

  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

export function endpointWithPath(endpointUrl, endpointPath) {
  if (!endpointUrl) return endpointPath || '-';
  if (!endpointPath) return endpointUrl;

  const normalizedBase = endpointUrl.endsWith('/') ? endpointUrl.slice(0, -1) : endpointUrl;
  const normalizedPath = endpointPath.startsWith('/') ? endpointPath : `/${endpointPath}`;
  return `${normalizedBase}${normalizedPath}`;
}

export function getEndpointHost(endpointUrl, fallback = 'unknown-host') {
  try {
    return new URL(endpointUrl).hostname;
  } catch (_error) {
    return fallback;
  }
}
