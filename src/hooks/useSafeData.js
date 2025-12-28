/**
 * useSafeData Hook
 *
 * Custom React hook for safe data fetching with built-in error handling,
 * loading states, and automatic cleanup. Prevents common async issues.
 *
 * @module useSafeData
 */

import { useState, useEffect, useCallback, useRef } from 'react';

/**
 * Safe data fetching hook with error handling
 * @param {Function} fetchFn - Async function that fetches data
 * @param {any} defaultValue - Default value while loading or on error
 * @param {Object} options - Hook options
 * @param {Array} options.deps - Dependencies array (like useEffect)
 * @param {boolean} options.immediate - Fetch immediately on mount (default: true)
 * @param {Function} options.onSuccess - Success callback
 * @param {Function} options.onError - Error callback
 * @param {number} options.retryCount - Number of retries on error (default: 0)
 * @param {number} options.retryDelay - Delay between retries in ms (default: 1000)
 * @returns {Object} { data, loading, error, refetch, setData }
 *
 * @example
 * // Basic usage
 * const { data, loading, error } = useSafeData(
 *   () => apiClient.get('/users'),
 *   []
 * );
 *
 * @example
 * // With options
 * const { data, loading, error, refetch } = useSafeData(
 *   () => apiClient.get(`/users/${userId}`),
 *   null,
 *   {
 *     deps: [userId],
 *     immediate: true,
 *     onSuccess: (data) => console.log('Loaded:', data),
 *     onError: (error) => showNotification(error.message),
 *     retryCount: 3,
 *     retryDelay: 2000
 *   }
 * );
 */
export const useSafeData = (fetchFn, defaultValue = [], options = {}) => {
  const {
    deps = [],
    immediate = true,
    onSuccess,
    onError,
    retryCount = 0,
    retryDelay = 1000
  } = options;

  const [data, setData] = useState(defaultValue);
  const [loading, setLoading] = useState(immediate);
  const [error, setError] = useState(null);
  const [retryAttempt, setRetryAttempt] = useState(0);

  // Track if component is mounted to prevent state updates after unmount
  const mountedRef = useRef(true);
  const abortControllerRef = useRef(null);

  const loadData = useCallback(async (isRetry = false) => {
    if (!mountedRef.current) return;

    try {
      // Cancel previous request if exists
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }

      // Create new abort controller for this request
      abortControllerRef.current = new AbortController();

      if (!isRetry) {
        setLoading(true);
        setError(null);
      }

      console.log('[useSafeData] Fetching data...', { isRetry, attempt: retryAttempt });

      const result = await fetchFn();

      if (mountedRef.current) {
        // Validate result
        const validData = result !== null && result !== undefined ? result : defaultValue;

        setData(validData);
        setError(null);
        setLoading(false);
        setRetryAttempt(0);

        console.log('[useSafeData] Data loaded successfully');

        if (onSuccess) {
          try {
            onSuccess(validData);
          } catch (callbackError) {
            console.error('[useSafeData] onSuccess callback error:', callbackError);
          }
        }
      }
    } catch (e) {
      if (!mountedRef.current) return;

      // Ignore abort errors
      if (e.name === 'AbortError') {
        console.log('[useSafeData] Request aborted');
        return;
      }

      console.error('[useSafeData] Error fetching data:', e);

      // Retry logic
      if (retryAttempt < retryCount) {
        console.log(`[useSafeData] Retrying in ${retryDelay}ms... (${retryAttempt + 1}/${retryCount})`);

        setTimeout(() => {
          if (mountedRef.current) {
            setRetryAttempt(prev => prev + 1);
            loadData(true);
          }
        }, retryDelay);

        return;
      }

      // Final error state
      setError(e);
      setData(defaultValue);
      setLoading(false);
      setRetryAttempt(0);

      if (onError) {
        try {
          onError(e);
        } catch (callbackError) {
          console.error('[useSafeData] onError callback error:', callbackError);
        }
      }
    }
  }, [fetchFn, defaultValue, onSuccess, onError, retryCount, retryDelay, retryAttempt]);

  // Effect to fetch data on mount or when dependencies change
  useEffect(() => {
    if (immediate) {
      loadData();
    }

    // Cleanup function
    return () => {
      mountedRef.current = false;
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, [immediate, ...deps]);

  // Manual refetch function
  const refetch = useCallback(() => {
    setRetryAttempt(0);
    return loadData();
  }, [loadData]);

  return {
    data,
    loading,
    error,
    refetch,
    setData
  };
};

/**
 * Safe polling hook - fetches data repeatedly at intervals
 * @param {Function} fetchFn - Async function that fetches data
 * @param {number} interval - Polling interval in ms
 * @param {any} defaultValue - Default value
 * @param {Object} options - Hook options (same as useSafeData)
 * @returns {Object} { data, loading, error, refetch, setData, startPolling, stopPolling, isPolling }
 *
 * @example
 * const { data, isPolling, startPolling, stopPolling } = useSafePolling(
 *   () => apiClient.get('/status'),
 *   5000, // Poll every 5 seconds
 *   { status: 'unknown' }
 * );
 */
export const useSafePolling = (fetchFn, interval, defaultValue = [], options = {}) => {
  const [isPolling, setIsPolling] = useState(false);
  const intervalRef = useRef(null);

  const result = useSafeData(fetchFn, defaultValue, {
    ...options,
    immediate: false
  });

  const startPolling = useCallback(() => {
    if (intervalRef.current) return; // Already polling

    setIsPolling(true);

    // Initial fetch
    result.refetch();

    // Set up interval
    intervalRef.current = setInterval(() => {
      result.refetch();
    }, interval);

    console.log(`[useSafePolling] Started polling every ${interval}ms`);
  }, [interval, result]);

  const stopPolling = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
      setIsPolling(false);
      console.log('[useSafePolling] Stopped polling');
    }
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopPolling();
    };
  }, [stopPolling]);

  return {
    ...result,
    isPolling,
    startPolling,
    stopPolling
  };
};

/**
 * Safe mutation hook - for POST/PUT/DELETE operations
 * @param {Function} mutateFn - Async function that performs mutation
 * @param {Object} options - Hook options
 * @param {Function} options.onSuccess - Success callback
 * @param {Function} options.onError - Error callback
 * @returns {Object} { mutate, loading, error, data, reset }
 *
 * @example
 * const { mutate, loading, error } = useSafeMutation(
 *   (userData) => apiClient.post('/users', userData),
 *   {
 *     onSuccess: (data) => {
 *       showNotification('User created!');
 *       navigate('/users');
 *     },
 *     onError: (error) => showNotification(error.message)
 *   }
 * );
 *
 * // Use it
 * mutate({ name: 'John', email: 'john@example.com' });
 */
export const useSafeMutation = (mutateFn, options = {}) => {
  const { onSuccess, onError } = options;

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const mountedRef = useRef(true);

  useEffect(() => {
    return () => {
      mountedRef.current = false;
    };
  }, []);

  const mutate = useCallback(async (...args) => {
    if (!mountedRef.current) return;

    try {
      setLoading(true);
      setError(null);

      console.log('[useSafeMutation] Executing mutation...');

      const result = await mutateFn(...args);

      if (mountedRef.current) {
        setData(result);
        setLoading(false);

        console.log('[useSafeMutation] Mutation successful');

        if (onSuccess) {
          try {
            onSuccess(result);
          } catch (callbackError) {
            console.error('[useSafeMutation] onSuccess callback error:', callbackError);
          }
        }

        return result;
      }
    } catch (e) {
      if (!mountedRef.current) return;

      console.error('[useSafeMutation] Mutation error:', e);

      setError(e);
      setData(null);
      setLoading(false);

      if (onError) {
        try {
          onError(e);
        } catch (callbackError) {
          console.error('[useSafeMutation] onError callback error:', callbackError);
        }
      }

      throw e;
    }
  }, [mutateFn, onSuccess, onError]);

  const reset = useCallback(() => {
    setData(null);
    setError(null);
    setLoading(false);
  }, []);

  return {
    mutate,
    loading,
    error,
    data,
    reset
  };
};

export default useSafeData;
