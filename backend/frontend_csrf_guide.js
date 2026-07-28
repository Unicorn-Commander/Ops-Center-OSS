/**
 * Frontend CSRF Integration Guide for UC-1 Pro Ops Center
 *
 * This file contains examples of how to integrate CSRF protection
 * in the React frontend application.
 */

// ============================================================================
// METHOD 1: React Context Provider (Recommended)
// ============================================================================

import React, { createContext, useContext, useEffect, useState } from 'react';

// Create CSRF context
const CsrfContext = createContext(null);

/**
 * CSRF Provider Component
 * Wrap your app with this to provide CSRF token to all components
 */
export function CsrfProvider({ children }) {
    const [csrfToken, setCsrfToken] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // Fetch CSRF token after authentication
        const fetchCsrfToken = async () => {
            try {
                const response = await fetch('/api/v1/auth/csrf-token', {
                    credentials: 'include'  // Include session cookie
                });

                if (response.ok) {
                    const data = await response.json();
                    setCsrfToken(data.csrf_token);
                } else {
                    console.warn('Failed to fetch CSRF token');
                }
            } catch (error) {
                console.error('Error fetching CSRF token:', error);
            } finally {
                setLoading(false);
            }
        };

        fetchCsrfToken();
    }, []);

    return (
        <CsrfContext.Provider value={{ csrfToken, loading }}>
            {children}
        </CsrfContext.Provider>
    );
}

/**
 * Hook to access CSRF token
 */
export function useCsrf() {
    const context = useContext(CsrfContext);
    if (!context) {
        throw new Error('useCsrf must be used within CsrfProvider');
    }
    return context;
}

// Usage in App.js:
/*
function App() {
    return (
        <AuthProvider>
            <CsrfProvider>
                <YourComponents />
            </CsrfProvider>
        </AuthProvider>
    );
}
*/

// Usage in components:
/*
function MyComponent() {
    const { csrfToken, loading } = useCsrf();

    const handleSubmit = async (data) => {
        if (loading) return;

        const response = await fetch('/api/v1/landing/config', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-Token': csrfToken
            },
            credentials: 'include',
            body: JSON.stringify(data)
        });

        // Handle response...
    };

    return <form onSubmit={handleSubmit}>...</form>;
}
*/

// ============================================================================
// METHOD 2: Utility Functions
// ============================================================================

/**
 * Get CSRF token from cookie
 * Cookie is automatically set by backend after authentication
 */
export function getCsrfTokenFromCookie() {
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
        const [name, value] = cookie.trim().split('=');
        if (name === 'csrf_token') {
            return value;
        }
    }
    return null;
}

/**
 * Fetch CSRF token from API
 * Alternative to reading from cookie
 */
export async function fetchCsrfToken() {
    try {
        const response = await fetch('/api/v1/auth/csrf-token', {
            credentials: 'include'
        });

        if (!response.ok) {
            throw new Error('Failed to fetch CSRF token');
        }

        const data = await response.json();
        return data.csrf_token;
    } catch (error) {
        console.error('Error fetching CSRF token:', error);
        return null;
    }
}

/**
 * Make a CSRF-protected request
 * Wrapper function that automatically includes CSRF token
 */
export async function protectedFetch(url, options = {}) {
    const csrfToken = getCsrfTokenFromCookie();

    if (!csrfToken && ['POST', 'PUT', 'DELETE', 'PATCH'].includes(options.method?.toUpperCase())) {
        throw new Error('CSRF token not found. Please login first.');
    }

    const headers = {
        ...options.headers,
        'X-CSRF-Token': csrfToken
    };

    return fetch(url, {
        ...options,
        headers,
        credentials: 'include'
    });
}

// Usage:
/*
try {
    const response = await protectedFetch('/api/v1/landing/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });

    if (response.ok) {
        const result = await response.json();
        console.log('Success:', result);
    }
} catch (error) {
    console.error('Request failed:', error);
}
*/

// ============================================================================
// METHOD 3: Axios Integration
// ============================================================================

import axios from 'axios';

/**
 * Configure axios globally for CSRF protection
 */
export function setupAxiosCsrf() {
    // Enable credentials for all requests
    axios.defaults.withCredentials = true;

    // Add request interceptor to include CSRF token
    axios.interceptors.request.use(
        (config) => {
            // Only add CSRF token for state-changing methods
            if (['post', 'put', 'delete', 'patch'].includes(config.method)) {
                const csrfToken = getCsrfTokenFromCookie();

                if (csrfToken) {
                    config.headers['X-CSRF-Token'] = csrfToken;
                } else {
                    console.warn('CSRF token not found for request:', config.url);
                }
            }

            return config;
        },
        (error) => {
            return Promise.reject(error);
        }
    );

    // Add response interceptor for CSRF error handling
    axios.interceptors.response.use(
        (response) => response,
        async (error) => {
            if (error.response?.status === 403 &&
                error.response?.data?.detail?.includes('CSRF')) {

                console.warn('CSRF validation failed, refreshing token...');

                // Try to refresh CSRF token
                try {
                    const newToken = await fetchCsrfToken();

                    if (newToken) {
                        // Retry the original request with new token
                        error.config.headers['X-CSRF-Token'] = newToken;
                        return axios.request(error.config);
                    }
                } catch (refreshError) {
                    console.error('Failed to refresh CSRF token:', refreshError);
                }
            }

            return Promise.reject(error);
        }
    );
}

// Call this in your app initialization:
/*
// In App.js or index.js
setupAxiosCsrf();

// Then use axios normally:
axios.post('/api/v1/landing/config', data)
    .then(response => console.log(response.data))
    .catch(error => console.error(error));
*/

// ============================================================================
// METHOD 4: Custom Hook for API Calls
// ============================================================================

/**
 * Custom hook for making CSRF-protected API calls
 */
export function useProtectedApi() {
    const { csrfToken } = useCsrf();

    const request = async (url, options = {}) => {
        if (!csrfToken && ['POST', 'PUT', 'DELETE', 'PATCH'].includes(options.method?.toUpperCase())) {
            throw new Error('CSRF token not available');
        }

        const headers = {
            'Content-Type': 'application/json',
            ...options.headers,
            'X-CSRF-Token': csrfToken
        };

        const response = await fetch(url, {
            ...options,
            headers,
            credentials: 'include'
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Request failed');
        }

        return response.json();
    };

    return {
        get: (url, options) => request(url, { ...options, method: 'GET' }),
        post: (url, data, options) => request(url, {
            ...options,
            method: 'POST',
            body: JSON.stringify(data)
        }),
        put: (url, data, options) => request(url, {
            ...options,
            method: 'PUT',
            body: JSON.stringify(data)
        }),
        delete: (url, options) => request(url, { ...options, method: 'DELETE' }),
    };
}

// Usage:
/*
function MyComponent() {
    const api = useProtectedApi();
    const [loading, setLoading] = useState(false);

    const handleUpdate = async (newConfig) => {
        setLoading(true);
        try {
            const result = await api.post('/api/v1/landing/config', newConfig);
            console.log('Updated:', result);
        } catch (error) {
            console.error('Update failed:', error);
        } finally {
            setLoading(false);
        }
    };

    return <button onClick={() => handleUpdate(data)}>Update</button>;
}
*/

// ============================================================================
// METHOD 5: Form Submission with CSRF
// ============================================================================

/**
 * Form component with CSRF protection
 */
export function CsrfProtectedForm({ action, method = 'POST', onSubmit, children }) {
    const { csrfToken } = useCsrf();

    const handleSubmit = async (e) => {
        e.preventDefault();

        const formData = new FormData(e.target);
        const data = Object.fromEntries(formData);

        try {
            const response = await fetch(action, {
                method,
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': csrfToken
                },
                credentials: 'include',
                body: JSON.stringify(data)
            });

            if (response.ok) {
                const result = await response.json();
                onSubmit?.(result);
            } else {
                const error = await response.json();
                console.error('Form submission failed:', error);
            }
        } catch (error) {
            console.error('Form submission error:', error);
        }
    };

    return (
        <form onSubmit={handleSubmit}>
            {children}
        </form>
    );
}

// Usage:
/*
<CsrfProtectedForm
    action="/api/v1/landing/config"
    method="POST"
    onSubmit={(result) => console.log('Success:', result)}
>
    <input name="title" placeholder="Title" />
    <input name="description" placeholder="Description" />
    <button type="submit">Submit</button>
</CsrfProtectedForm>
*/

// ============================================================================
// Error Handling
// ============================================================================

/**
 * Handle CSRF validation errors
 */
export async function handleCsrfError(error, retryFn) {
    if (error.response?.status === 403 &&
        error.response?.data?.detail?.includes('CSRF')) {

        console.warn('CSRF validation failed, attempting to refresh token...');

        try {
            // Refresh CSRF token
            const newToken = await fetchCsrfToken();

            if (newToken && retryFn) {
                // Retry the original request
                return await retryFn(newToken);
            }
        } catch (refreshError) {
            console.error('Failed to refresh CSRF token:', refreshError);
            // Redirect to login or show error
            window.location.href = '/auth/login';
        }
    }

    throw error;
}

// Usage:
/*
try {
    await protectedFetch('/api/v1/some-endpoint', {
        method: 'POST',
        body: JSON.stringify(data)
    });
} catch (error) {
    await handleCsrfError(error, async (newToken) => {
        // Retry with new token
        return protectedFetch('/api/v1/some-endpoint', {
            method: 'POST',
            headers: { 'X-CSRF-Token': newToken },
            body: JSON.stringify(data)
        });
    });
}
*/

// ============================================================================
// Testing Utilities
// ============================================================================

/**
 * Test CSRF protection in browser console
 */
export async function testCsrfProtection() {
    console.log('=== CSRF Protection Test ===');

    // Test 1: Get CSRF token
    console.log('\n1. Fetching CSRF token...');
    const token = await fetchCsrfToken();
    console.log('Token:', token);

    // Test 2: GET request (should work without CSRF)
    console.log('\n2. Testing GET request (no CSRF required)...');
    try {
        const response = await fetch('/api/v1/deployment/config', {
            credentials: 'include'
        });
        console.log('GET Status:', response.status);
    } catch (error) {
        console.error('GET failed:', error);
    }

    // Test 3: POST without CSRF (should fail)
    console.log('\n3. Testing POST without CSRF token (should fail)...');
    try {
        const response = await fetch('/api/v1/landing/config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ test: true })
        });
        console.log('POST without CSRF Status:', response.status);
    } catch (error) {
        console.error('POST without CSRF failed (expected):', error);
    }

    // Test 4: POST with CSRF (should succeed)
    console.log('\n4. Testing POST with CSRF token (should succeed)...');
    try {
        const response = await protectedFetch('/api/v1/landing/config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ test: true })
        });
        console.log('POST with CSRF Status:', response.status);
    } catch (error) {
        console.error('POST with CSRF failed:', error);
    }

    console.log('\n=== Test Complete ===');
}

// Run in browser console:
// testCsrfProtection()

// ============================================================================
// Export all utilities
// ============================================================================

export default {
    CsrfProvider,
    useCsrf,
    getCsrfTokenFromCookie,
    fetchCsrfToken,
    protectedFetch,
    setupAxiosCsrf,
    useProtectedApi,
    CsrfProtectedForm,
    handleCsrfError,
    testCsrfProtection
};
