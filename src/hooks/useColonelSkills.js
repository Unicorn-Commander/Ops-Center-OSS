import { useState, useEffect, useCallback } from 'react';

/**
 * Hook for managing Colonel skills: listing and toggling.
 */
export default function useColonelSkills() {
  const [skills, setSkills] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchSkills = useCallback(async () => {
    try {
      setLoading(true);
      const res = await fetch('/api/v1/colonel/skills');
      if (!res.ok) throw new Error(`Failed: ${res.status}`);
      const data = await res.json();
      setSkills(data.skills || []);
      setError(null);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, []);

  const toggleSkill = useCallback(async (skillId) => {
    try {
      const res = await fetch(`/api/v1/colonel/skills/${skillId}/toggle`, { method: 'PUT' });
      if (!res.ok) throw new Error(`Failed: ${res.status}`);
      const data = await res.json();
      setSkills(prev =>
        prev.map(s => s.id === skillId ? { ...s, enabled: data.enabled } : s)
      );
      return data.enabled;
    } catch (e) {
      setError(e.message);
      return null;
    }
  }, []);

  useEffect(() => {
    fetchSkills();
  }, [fetchSkills]);

  return {
    skills,
    loading,
    error,
    toggleSkill,
    refreshSkills: fetchSkills,
    enabledCount: skills.filter(s => s.enabled).length,
    totalCount: skills.length,
  };
}
