import { useState, useEffect, useRef } from 'react';
import PropTypes from 'prop-types';

/**
 * OptimizedImage Component
 *
 * Features:
 * - Lazy loading with Intersection Observer
 * - WebP format with fallback to original
 * - Blur placeholder while loading
 * - Responsive image loading
 * - Automatic format detection
 */
export function OptimizedImage({
  src,
  alt,
  className = '',
  width,
  height,
  loading = 'lazy',
  placeholder = true,
  objectFit = 'contain',
  ...props
}) {
  const [isLoaded, setIsLoaded] = useState(false);
  const [isInView, setIsInView] = useState(false);
  const [error, setError] = useState(false);
  const imgRef = useRef(null);

  // Intersection Observer for lazy loading
  useEffect(() => {
    if (!imgRef.current || loading !== 'lazy') {
      setIsInView(true);
      return;
    }

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsInView(true);
          observer.disconnect();
        }
      },
      {
        rootMargin: '50px', // Start loading 50px before image comes into view
        threshold: 0.01
      }
    );

    observer.observe(imgRef.current);

    return () => {
      observer.disconnect();
    };
  }, [loading]);

  // Generate WebP source if original is PNG/JPG
  const getWebPSrc = (originalSrc) => {
    if (!originalSrc) return null;

    // Check if image is already WebP
    if (originalSrc.endsWith('.webp')) return null;

    // Only convert PNG, JPG, JPEG to WebP
    if (/\.(png|jpg|jpeg)$/i.test(originalSrc)) {
      return originalSrc.replace(/\.(png|jpg|jpeg)$/i, '.webp');
    }

    return null;
  };

  const webpSrc = getWebPSrc(src);

  // Handle image load
  const handleLoad = () => {
    setIsLoaded(true);
    setError(false);
  };

  // Handle image error (fallback to original if WebP fails)
  const handleError = () => {
    setError(true);
  };

  return (
    <div
      ref={imgRef}
      className={`optimized-image-wrapper ${className}`}
      style={{
        position: 'relative',
        display: 'inline-block',
        width: width || '100%',
        height: height || 'auto',
        overflow: 'hidden'
      }}
    >
      {/* Blur placeholder */}
      {placeholder && !isLoaded && (
        <div
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            width: '100%',
            height: '100%',
            background: 'linear-gradient(135deg, #f0f0f0 0%, #e0e0e0 100%)',
            filter: 'blur(10px)',
            animation: 'pulse 1.5s ease-in-out infinite'
          }}
        />
      )}

      {/* Actual image */}
      {isInView && (
        <picture>
          {/* WebP source for modern browsers */}
          {webpSrc && !error && (
            <source srcSet={webpSrc} type="image/webp" />
          )}

          {/* Fallback to original format */}
          <img
            src={src}
            alt={alt}
            width={width}
            height={height}
            loading={loading}
            onLoad={handleLoad}
            onError={handleError}
            style={{
              opacity: isLoaded ? 1 : 0,
              transition: 'opacity 0.3s ease-in-out',
              width: '100%',
              height: '100%',
              objectFit: objectFit,
              display: 'block'
            }}
            {...props}
          />
        </picture>
      )}

      {/* Inline styles for pulse animation */}
      <style>
        {`
          @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
          }
        `}
      </style>
    </div>
  );
}

OptimizedImage.propTypes = {
  src: PropTypes.string.isRequired,
  alt: PropTypes.string.isRequired,
  className: PropTypes.string,
  width: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
  height: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
  loading: PropTypes.oneOf(['lazy', 'eager']),
  placeholder: PropTypes.bool,
  objectFit: PropTypes.oneOf(['contain', 'cover', 'fill', 'none', 'scale-down'])
};

export default OptimizedImage;
