import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';

const ColonelContext = createContext(null);

export function useColonel() {
  const ctx = useContext(ColonelContext);
  if (!ctx) throw new Error('useColonel must be used within ColonelProvider');
  return ctx;
}

export function ColonelProvider({ children }) {
  const [config, setConfig] = useState(null);
  const [online, setOnline] = useState(false);
  const [onboarded, setOnboarded] = useState(null); // null = loading
  const [activeSessions, setActiveSessions] = useState(0);
  const [skillsLoaded, setSkillsLoaded] = useState(0);
  const [memoryEntries, setMemoryEntries] = useState(0);

  const refreshStatus = useCallback(async () => {
    try {
      const res = await fetch('/api/v1/colonel/status');
      if (!res.ok) return;
      const data = await res.json();
      setOnline(data.online);
      setConfig(data.config || null);
      setOnboarded(data.config?.onboarded ?? false);
      setActiveSessions(data.active_sessions || 0);
      setSkillsLoaded(data.skills_loaded || 0);
      setMemoryEntries(data.memory_entries || 0);
    } catch {
      setOnline(false);
    }
  }, []);

  const checkOnboarded = useCallback(async () => {
    try {
      const res = await fetch('/api/v1/colonel/onboarded');
      if (res.ok) {
        const data = await res.json();
        setOnboarded(data.onboarded);
        return data.onboarded;
      }
    } catch {
      // ignore
    }
    return false;
  }, []);

  useEffect(() => {
    refreshStatus();
    const interval = setInterval(refreshStatus, 60000);
    return () => clearInterval(interval);
  }, [refreshStatus]);

  const value = {
    config,
    online,
    onboarded,
    activeSessions,
    skillsLoaded,
    memoryEntries,
    refreshStatus,
    checkOnboarded,
  };

  return (
    <ColonelContext.Provider value={value}>
      {children}
    </ColonelContext.Provider>
  );
}
