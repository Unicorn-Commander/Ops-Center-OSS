import React from 'react';
import { Link } from 'react-router-dom';

/**
 * NotFound - catch-all 404 page.
 *
 * Rendered for any URL that matches no route. Before this existed, unmatched
 * URLs rendered a completely blank page (no route matched, ErrorBoundary saw
 * nothing to catch), which read as "the site is broken".
 */
export default function NotFound({ admin = false }) {
  const home = admin ? '/admin/' : '/';
  return (
    <div className="min-h-[60vh] flex flex-col items-center justify-center text-center px-6 py-16">
      <div className="text-7xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
        404
      </div>
      <h1 className="mt-4 text-2xl font-semibold text-white">Page not found</h1>
      <p className="mt-2 max-w-md text-gray-400">
        The page you&apos;re looking for doesn&apos;t exist or may have moved.
      </p>
      <div className="mt-8 flex items-center gap-3">
        <Link
          to={home}
          className="px-5 py-2.5 rounded-lg font-medium text-white bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 transition-colors"
        >
          {admin ? 'Back to Dashboard' : 'Back to Home'}
        </Link>
        <button
          onClick={() => window.history.back()}
          className="px-5 py-2.5 rounded-lg font-medium text-gray-300 border border-gray-600 hover:bg-white/5 transition-colors"
        >
          Go Back
        </button>
      </div>
    </div>
  );
}
