/**
 * Colonel API service layer.
 * Centralizes all REST API calls for The Colonel system.
 */

const BASE = '/api/v1/colonel';

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    credentials: 'include',
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(text || `Colonel API error: ${res.status}`);
  }
  return res.json();
}

// ─── Status & Config ─────────────────────────────────────────────────

export async function getStatus() {
  return request('/status');
}

export async function getConfig() {
  return request('/config');
}

export async function updateConfig(config) {
  return request('/config', {
    method: 'PUT',
    body: JSON.stringify(config),
  });
}

export async function checkOnboarded() {
  return request('/onboarded');
}

// ─── Onboarding ─────────────────────────────────────────────────────

export async function detectEnvironment() {
  return request('/detect');
}

export async function onboard(config) {
  return request('/onboard', {
    method: 'POST',
    body: JSON.stringify(config),
  });
}

// ─── Skills ─────────────────────────────────────────────────────────

export async function getSkills() {
  return request('/skills');
}

export async function toggleSkill(skillId) {
  return request(`/skills/${skillId}/toggle`, { method: 'PUT' });
}

// ─── Sessions ───────────────────────────────────────────────────────

export async function getSessions() {
  return request('/sessions');
}

export async function getSession(sessionId) {
  return request(`/sessions/${sessionId}`);
}

// ─── Memory ─────────────────────────────────────────────────────────

export async function searchMemory(query, limit = 10) {
  return request(`/memory/search?q=${encodeURIComponent(query)}&limit=${limit}`);
}

// ─── Audit ──────────────────────────────────────────────────────────

export async function getAuditLog(limit = 20, offset = 0) {
  return request(`/audit?limit=${limit}&offset=${offset}`);
}

// ─── The General (Multi-Colonel) ────────────────────────────────────

export async function getGeneralStatus() {
  try {
    return await request('/general/status');
  } catch {
    // General endpoint may not exist yet - return mock structure
    return {
      available: false,
      colonels: [],
      connected_count: 0,
    };
  }
}

export async function getColonelRegistry() {
  try {
    return await request('/general/colonels');
  } catch {
    return { colonels: [] };
  }
}
