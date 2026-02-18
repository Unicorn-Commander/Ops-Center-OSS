import { useState, useCallback } from 'react';

/**
 * Hook for searching Colonel's semantic memory.
 */
export default function useColonelMemory() {
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const search = useCallback(async (query, limit = 10) => {
    if (!query || query.trim().length < 2) {
      setResults([]);
      return [];
    }
    try {
      setLoading(true);
      setError(null);
      const res = await fetch(
        `/api/v1/colonel/memory/search?q=${encodeURIComponent(query)}&limit=${limit}`
      );
      if (!res.ok) throw new Error(`Search failed: ${res.status}`);
      const data = await res.json();
      const items = data.results || [];
      setResults(items);
      return items;
    } catch (e) {
      setError(e.message);
      return [];
    } finally {
      setLoading(false);
    }
  }, []);

  const clear = useCallback(() => {
    setResults([]);
    setError(null);
  }, []);

  return { results, loading, error, search, clear };
}
