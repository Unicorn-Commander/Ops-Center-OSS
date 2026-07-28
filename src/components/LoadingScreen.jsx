import React from 'react';

/**
 * Branded full-screen loader. Used as the Suspense fallback for lazy routes and
 * while auth is being checked. On-brand (violet/cyan), lightweight, and
 * respects prefers-reduced-motion via the shared design-system layer.
 */
export default function LoadingScreen({ label = 'Loading', sublabel = 'Preparing your console…' }) {
  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background:
          'radial-gradient(1200px 600px at 50% -10%, rgba(124,58,237,0.10), transparent 60%), linear-gradient(180deg, #070912 0%, #090b13 100%)',
      }}
    >
      <div style={{ textAlign: 'center' }}>
        <div
          aria-hidden
          style={{
            width: 56,
            height: 56,
            margin: '0 auto 20px',
            borderRadius: '50%',
            background:
              'conic-gradient(from 0deg, #22d3ee, #7c3aed, #a855f7, #22d3ee)',
            WebkitMask:
              'radial-gradient(farthest-side, transparent calc(100% - 4px), #000 0)',
            mask: 'radial-gradient(farthest-side, transparent calc(100% - 4px), #000 0)',
            animation: 'uc-spin 0.9s linear infinite',
          }}
        />
        <div
          style={{
            fontSize: 16,
            fontWeight: 600,
            letterSpacing: '-0.01em',
            color: '#f3f5fb',
            marginBottom: 6,
          }}
        >
          {label}
        </div>
        <div style={{ fontSize: 13, color: '#7c8aa3' }}>{sublabel}</div>
      </div>
      <style>{`@keyframes uc-spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}
