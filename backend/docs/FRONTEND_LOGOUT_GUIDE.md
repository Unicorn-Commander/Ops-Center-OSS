# Frontend Logout Integration - Quick Guide

## TL;DR

When user clicks logout, call the backend API and redirect to the returned SSO logout URL:

```javascript
async function logout() {
  const response = await fetch('/api/v1/auth/logout', {
    method: 'POST',
    credentials: 'include'
  });

  if (response.ok) {
    const data = await response.json();
    window.location.href = data.sso_logout_url; // Redirect to Keycloak
  }
}
```

## API Endpoint

**POST** `/api/v1/auth/logout`

### Request

```http
POST /api/v1/auth/logout HTTP/1.1
Content-Type: application/json
Cookie: session=<user-session-cookie>
```

No request body needed.

### Response

```json
{
  "message": "Logged out successfully",
  "sso_logout_url": "https://auth.your-domain.com/realms/master/protocol/openid-connect/logout?redirect_uri=https://your-domain.com"
}
```

## Implementation Examples

### Vanilla JavaScript

```javascript
const logoutButton = document.getElementById('logout-btn');

logoutButton.addEventListener('click', async () => {
  try {
    const response = await fetch('/api/v1/auth/logout', {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json'
      }
    });

    if (response.ok) {
      const data = await response.json();

      // Optional: Clear local storage
      localStorage.clear();
      sessionStorage.clear();

      // Redirect to Keycloak logout
      window.location.href = data.sso_logout_url;
    } else {
      console.error('Logout failed');
      window.location.href = '/';
    }
  } catch (error) {
    console.error('Logout error:', error);
    window.location.href = '/';
  }
});
```

### React + TypeScript

```typescript
import React from 'react';
import { useNavigate } from 'react-router-dom';

interface LogoutResponse {
  message: string;
  sso_logout_url: string;
}

export const LogoutButton: React.FC = () => {
  const navigate = useNavigate();

  const handleLogout = async () => {
    try {
      const response = await fetch('/api/v1/auth/logout', {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data: LogoutResponse = await response.json();

        // Clear local state
        localStorage.clear();
        sessionStorage.clear();

        // Redirect to SSO logout
        window.location.href = data.sso_logout_url;
      } else {
        console.error('Logout failed:', response.statusText);
        navigate('/');
      }
    } catch (error) {
      console.error('Logout error:', error);
      navigate('/');
    }
  };

  return (
    <button onClick={handleLogout} className="logout-btn">
      Logout
    </button>
  );
};
```

### React with Custom Hook

```typescript
// hooks/useAuth.ts
import { useCallback } from 'react';

interface LogoutResponse {
  message: string;
  sso_logout_url: string;
}

export function useAuth() {
  const logout = useCallback(async () => {
    try {
      const response = await fetch('/api/v1/auth/logout', {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data: LogoutResponse = await response.json();

        // Clear local state
        localStorage.clear();
        sessionStorage.clear();

        // Redirect to Keycloak
        window.location.href = data.sso_logout_url;
      } else {
        throw new Error('Logout failed');
      }
    } catch (error) {
      console.error('Logout error:', error);
      window.location.href = '/';
    }
  }, []);

  return { logout };
}

// Usage in component
import { useAuth } from './hooks/useAuth';

function MyComponent() {
  const { logout } = useAuth();

  return <button onClick={logout}>Logout</button>;
}
```

### Vue 3 (Composition API)

```typescript
<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';

interface LogoutResponse {
  message: string;
  sso_logout_url: string;
}

const router = useRouter();
const isLoading = ref(false);

const logout = async () => {
  isLoading.value = true;

  try {
    const response = await fetch('/api/v1/auth/logout', {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json'
      }
    });

    if (response.ok) {
      const data: LogoutResponse = await response.json();

      // Clear local state
      localStorage.clear();
      sessionStorage.clear();

      // Redirect to Keycloak
      window.location.href = data.sso_logout_url;
    } else {
      console.error('Logout failed');
      router.push('/');
    }
  } catch (error) {
    console.error('Logout error:', error);
    router.push('/');
  } finally {
    isLoading.value = false;
  }
};
</script>

<template>
  <button @click="logout" :disabled="isLoading">
    {{ isLoading ? 'Logging out...' : 'Logout' }}
  </button>
</template>
```

### Vue 2 (Options API)

```javascript
export default {
  methods: {
    async logout() {
      try {
        const response = await fetch('/api/v1/auth/logout', {
          method: 'POST',
          credentials: 'include',
          headers: {
            'Content-Type': 'application/json'
          }
        });

        if (response.ok) {
          const data = await response.json();

          // Clear Vuex store if used
          this.$store.commit('clearAuth');

          // Clear local storage
          localStorage.clear();
          sessionStorage.clear();

          // Redirect to Keycloak
          window.location.href = data.sso_logout_url;
        } else {
          console.error('Logout failed');
          this.$router.push('/');
        }
      } catch (error) {
        console.error('Logout error:', error);
        this.$router.push('/');
      }
    }
  }
}
```

### Angular

```typescript
// auth.service.ts
import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { firstValueFrom } from 'rxjs';

interface LogoutResponse {
  message: string;
  sso_logout_url: string;
}

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  constructor(
    private http: HttpClient,
    private router: Router
  ) {}

  async logout(): Promise<void> {
    try {
      const response = await firstValueFrom(
        this.http.post<LogoutResponse>(
          '/api/v1/auth/logout',
          {},
          { withCredentials: true }
        )
      );

      // Clear local storage
      localStorage.clear();
      sessionStorage.clear();

      // Redirect to Keycloak
      window.location.href = response.sso_logout_url;
    } catch (error) {
      console.error('Logout error:', error);
      this.router.navigate(['/']);
    }
  }
}

// logout.component.ts
import { Component } from '@angular/core';
import { AuthService } from './auth.service';

@Component({
  selector: 'app-logout-button',
  template: `
    <button (click)="logout()" class="logout-btn">
      Logout
    </button>
  `
})
export class LogoutButtonComponent {
  constructor(private authService: AuthService) {}

  async logout(): Promise<void> {
    await this.authService.logout();
  }
}
```

### Svelte

```svelte
<script lang="ts">
  interface LogoutResponse {
    message: string;
    sso_logout_url: string;
  }

  let isLoading = false;

  async function logout() {
    isLoading = true;

    try {
      const response = await fetch('/api/v1/auth/logout', {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data: LogoutResponse = await response.json();

        // Clear local storage
        localStorage.clear();
        sessionStorage.clear();

        // Redirect to Keycloak
        window.location.href = data.sso_logout_url;
      } else {
        console.error('Logout failed');
        window.location.href = '/';
      }
    } catch (error) {
      console.error('Logout error:', error);
      window.location.href = '/';
    } finally {
      isLoading = false;
    }
  }
</script>

<button on:click={logout} disabled={isLoading}>
  {isLoading ? 'Logging out...' : 'Logout'}
</button>
```

## What Happens After Redirect

```
1. Browser redirects to:
   https://auth.your-domain.com/realms/master/protocol/openid-connect/logout?redirect_uri=https://your-domain.com

2. Keycloak:
   - Validates redirect_uri
   - Ends SSO session
   - Clears cookies
   - Redirects back to: https://your-domain.com

3. User lands on homepage, fully logged out
```

## Important Notes

### 1. Use `credentials: 'include'`

Always include credentials to send session cookies:

```javascript
fetch('/api/v1/auth/logout', {
  credentials: 'include'  // ← Required!
})
```

### 2. Clear Local State (Recommended)

Clear any cached data before redirect:

```javascript
localStorage.clear();
sessionStorage.clear();

// If using Redux, Vuex, etc.
store.dispatch('logout');
```

### 3. Use `window.location.href` (Not Router)

You MUST use `window.location.href` to redirect, not frontend router:

```javascript
// ✅ CORRECT
window.location.href = data.sso_logout_url;

// ❌ WRONG - Won't clear SSO session
router.push('/logout');
navigate('/logout');
this.$router.push('/logout');
```

### 4. Handle Errors Gracefully

Always have a fallback if logout fails:

```javascript
} catch (error) {
  console.error('Logout error:', error);
  // Fallback: redirect to home
  window.location.href = '/';
}
```

## Testing Checklist

- [ ] Clicking logout calls `/api/v1/auth/logout`
- [ ] Response contains `sso_logout_url` field
- [ ] Browser redirects to Keycloak
- [ ] Keycloak shows logout/redirect
- [ ] Browser redirects back to homepage
- [ ] User cannot access protected pages
- [ ] Local storage is cleared
- [ ] Session cookie is cleared
- [ ] Revisiting the app requires login

## Common Issues

### Issue: CORS Error

**Cause:** API not configured for credentials

**Solution:** Ensure backend CORS allows credentials:
```python
# Backend
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["https://your-domain.com"]
)
```

### Issue: 401 Unauthorized

**Cause:** Session expired or not authenticated

**Solution:** This is expected - redirect to login:
```javascript
if (response.status === 401) {
  window.location.href = '/login';
}
```

### Issue: Logout but Still Logged In

**Cause:** Not redirecting to `sso_logout_url`

**Solution:** Verify you're using:
```javascript
window.location.href = data.sso_logout_url;
```

## Quick Reference

| What | Value |
|------|-------|
| **Endpoint** | `POST /api/v1/auth/logout` |
| **Auth Required** | Yes (session cookie) |
| **Request Body** | None |
| **Response Field** | `sso_logout_url` |
| **Frontend Action** | `window.location.href = url` |
| **Keycloak URL** | https://auth.your-domain.com |
| **Realm** | master |
| **Redirect Back** | https://your-domain.com |

## Need Help?

- Backend Documentation: `/backend/docs/KEYCLOAK_SSO_LOGOUT.md`
- Full Implementation Guide: `/backend/KEYCLOAK_LOGOUT_IMPLEMENTATION.md`
- Test Script: `/backend/tests/test_logout_simple.sh`
- Keycloak Admin: https://auth.your-domain.com/admin

---

**Last Updated:** 2025-10-13
**Status:** ✅ Ready for Frontend Integration
