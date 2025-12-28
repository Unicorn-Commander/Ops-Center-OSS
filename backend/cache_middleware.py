"""
HTTP Cache Headers Middleware

Implements intelligent cache control headers for different resource types:
- Static assets: Long-term caching (1 year)
- API responses: Short-term caching (5 minutes)
- HTML: No cache (always revalidate)
- User-specific content: Private caching
- Public data: Public caching

Also implements ETag support for conditional requests
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.datastructures import Headers
import hashlib
import time
from typing import Optional


class CacheHeaderMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add intelligent cache control headers based on content type and route
    """

    def __init__(self, app):
        super().__init__(app)
        self.cache_metrics = {
            'hits': 0,
            'misses': 0,
            'etag_hits': 0
        }

    async def dispatch(self, request: Request, call_next):
        # Process the request
        response = await call_next(request)

        # Get path
        path = request.url.path

        # Determine cache strategy based on path and content type
        cache_control = self._get_cache_control(path, response.headers.get('content-type', ''))

        # Add cache control header
        if cache_control:
            response.headers['Cache-Control'] = cache_control

        # Add ETag for cacheable responses
        if self._should_add_etag(path, response.status_code):
            etag = self._generate_etag(response)
            if etag:
                response.headers['ETag'] = etag

                # Check if client has matching ETag
                if_none_match = request.headers.get('If-None-Match')
                if if_none_match == etag:
                    # Return 304 Not Modified
                    self.cache_metrics['etag_hits'] += 1
                    return Response(status_code=304, headers=response.headers)

        # Add Last-Modified header for static content
        if path.startswith('/assets/') or path.startswith('/logos/'):
            response.headers['Last-Modified'] = self._get_last_modified()

        # Add Vary header for content negotiation
        if path.startswith('/api/'):
            response.headers['Vary'] = 'Accept, Authorization'

        # Add security headers
        if not path.startswith('/api/'):
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-Frame-Options'] = 'SAMEORIGIN'
            response.headers['X-XSS-Protection'] = '1; mode=block'

        return response

    def _get_cache_control(self, path: str, content_type: str) -> Optional[str]:
        """
        Determine appropriate Cache-Control header based on path and content type
        """

        # Static assets in /assets/ - Long-term immutable cache
        if path.startswith('/assets/'):
            return 'public, max-age=31536000, immutable'

        # Logo and images - Long-term cache but revalidate
        if path.startswith('/logos/') or path.endswith(('.png', '.jpg', '.jpeg', '.svg', '.ico', '.webp')):
            return 'public, max-age=2592000, must-revalidate'

        # Fonts - Long-term cache
        if path.endswith(('.woff', '.woff2', '.ttf', '.eot')):
            return 'public, max-age=31536000, immutable'

        # CSS and JS bundles with hashes - Long-term immutable
        if (path.endswith('.css') or path.endswith('.js')) and '-' in path:
            return 'public, max-age=31536000, immutable'

        # Service worker - No cache (always fresh)
        if path.endswith('sw.js') or path.endswith('workbox-') or path == '/manifest.webmanifest':
            return 'no-cache, must-revalidate'

        # API - Static configuration endpoints (rarely change)
        if path in ['/api/v1/system/status', '/api/v1/service-urls', '/api/v1/deployment/config']:
            return 'public, max-age=3600, must-revalidate'  # 1 hour

        # API - Public data (short cache)
        if path.startswith('/api/v1/billing/plans') or path.startswith('/api/v1/organizations'):
            return 'public, max-age=300, must-revalidate'  # 5 minutes

        # API - User-specific data (private cache)
        if path.startswith('/api/v1/admin/') or path.startswith('/api/v1/account/'):
            return 'private, max-age=60, must-revalidate'  # 1 minute

        # API - General endpoints (short cache)
        if path.startswith('/api/'):
            return 'public, max-age=60, must-revalidate'  # 1 minute

        # HTML pages - No cache (always revalidate)
        if path.endswith('.html') or content_type == 'text/html':
            return 'no-cache, must-revalidate'

        # Default - No cache
        return 'no-store'

    def _should_add_etag(self, path: str, status_code: int) -> bool:
        """
        Determine if ETag should be added
        """
        # Only add ETags for successful responses
        if status_code != 200:
            return False

        # Add ETags for API responses
        if path.startswith('/api/'):
            return True

        # Add ETags for static assets
        if path.startswith('/assets/') or path.startswith('/logos/'):
            return True

        return False

    def _generate_etag(self, response: Response) -> Optional[str]:
        """
        Generate ETag from response body
        """
        try:
            # Get response body
            body = response.body if hasattr(response, 'body') else None
            if not body:
                return None

            # Generate hash
            etag = hashlib.md5(body).hexdigest()
            return f'"{etag}"'
        except Exception as e:
            # Don't break on ETag generation failure
            print(f"Failed to generate ETag: {e}")
            return None

    def _get_last_modified(self) -> str:
        """
        Get Last-Modified timestamp (using current time as placeholder)
        In production, this should be the actual file modification time
        """
        from email.utils import formatdate
        return formatdate(timeval=time.time(), localtime=False, usegmt=True)

    def get_metrics(self) -> dict:
        """
        Get cache metrics
        """
        total_requests = self.cache_metrics['hits'] + self.cache_metrics['misses']
        hit_rate = (self.cache_metrics['hits'] / total_requests * 100) if total_requests > 0 else 0

        return {
            'hits': self.cache_metrics['hits'],
            'misses': self.cache_metrics['misses'],
            'etag_hits': self.cache_metrics['etag_hits'],
            'total_requests': total_requests,
            'hit_rate_percent': round(hit_rate, 2)
        }


class CompressionMiddleware(BaseHTTPMiddleware):
    """
    Middleware to handle compression headers
    Note: Actual compression should be done by reverse proxy (Nginx/Traefik)
    """

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Add Vary header for compression
        vary_header = response.headers.get('Vary', '')
        if 'Accept-Encoding' not in vary_header:
            response.headers['Vary'] = f"{vary_header}, Accept-Encoding".strip(', ')

        return response
