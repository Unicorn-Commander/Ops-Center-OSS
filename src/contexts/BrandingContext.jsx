import React, { createContext, useContext, useState, useEffect } from 'react';

const BrandingContext = createContext({
  branding: null,
  loading: true,
  error: null
});

/**
 * BrandingProvider — fetches runtime branding from /api/v1/branding/config
 * and makes it available to the entire app.
 *
 * This runs on app mount, before any page renders, so branding is
 * available for the login page (unauthenticated) and all authenticated pages.
 */
export function BrandingProvider({ children }) {
  const [branding, setBranding] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;

    async function fetchBranding() {
      try {
        const response = await fetch('/api/v1/branding/config', {
          cache: 'no-cache'
        });

        if (!response.ok) {
          throw new Error(`Branding API returned ${response.status}`);
        }

        const data = await response.json();

        if (!cancelled) {
          setBranding(data);
          applyBrandingToDom(data);
          setLoading(false);
        }
      } catch (err) {
        if (!cancelled) {
          console.warn('Failed to load branding config, using defaults:', err.message);
          setError(err);
          // Use fallback values
          const fallback = {
            company_name: 'Ops-Center',
            page_title: 'Ops-Center',
            primary_color: '#7c3aed',
            logo_url: '/logos/ops-center-logo.png',
            tagline: 'Operations Center',
            subtitle: 'System Administration',
            sso_provider_name: 'SSO',
            sso_enabled: true
          };
          setBranding(fallback);
          applyBrandingToDom(fallback);
          setLoading(false);
        }
      }
    }

    fetchBranding();

    return () => { cancelled = true; };
  }, []);

  return (
    <BrandingContext.Provider value={{ branding, loading, error }}>
      {children}
    </BrandingContext.Provider>
  );
}

/**
 * Apply branding to the DOM (document title, theme-color meta, favicon).
 * Called from BrandingProvider after fetch completes.
 */
function applyBrandingToDom(branding) {
  if (!branding) return;

  // Page title
  document.title = branding.page_title || `${branding.company_name} — Operations Center`;

  // Theme color meta tag (for PWA / mobile status bar)
  const themeMeta = document.querySelector('meta[name="theme-color"]');
  if (themeMeta && branding.primary_color) {
    themeMeta.setAttribute('content', branding.primary_color);
  }

  // Favicon
  if (branding.favicon_url) {
    const faviconLink = document.querySelector('link[rel="icon"]');
    if (faviconLink) {
      faviconLink.setAttribute('href', branding.favicon_url);
    }
  }

  // OG tags
  updateMetaProperty('og:title', branding.og_title || branding.page_title);
  updateMetaProperty('og:description', branding.og_description || branding.tagline);
  if (branding.og_image) {
    updateMetaProperty('og:image', branding.og_image);
  }

  // Twitter tags
  updateMetaProperty('twitter:title', branding.og_title || branding.page_title);
  updateMetaProperty('twitter:description', branding.og_description || branding.tagline);
  if (branding.og_image) {
    updateMetaProperty('twitter:image', branding.og_image);
  }

  // CSS custom properties for theme colors
  if (branding.primary_color) {
    document.documentElement.style.setProperty('--brand-primary', branding.primary_color);
  }
}

function updateMetaProperty(property, content) {
  if (!content) return;
  let meta = document.querySelector(`meta[property="${property}"]`);
  if (!meta) {
    meta = document.createElement('meta');
    meta.setAttribute('property', property);
    document.head.appendChild(meta);
  }
  meta.setAttribute('content', content);
}

/**
 * Hook to access branding in any component.
 */
export function useBranding() {
  const context = useContext(BrandingContext);
  if (!context) {
    throw new Error('useBranding must be used within a BrandingProvider');
  }
  return context;
}

export default BrandingContext;
