/**
 * Touch Optimization Utilities
 *
 * Utilities for detecting and optimizing touch interactions
 * on mobile and tablet devices
 *
 * Features:
 * - Touch device detection
 * - Touch-friendly hover states
 * - Double-tap zoom prevention
 * - Screen size detection
 * - Viewport configuration
 * - Gesture handling
 *
 * Last Updated: October 24, 2025
 */

/**
 * Detect if the current device supports touch input
 * @returns {boolean} True if device supports touch
 */
export const isTouchDevice = () => {
  return (
    'ontouchstart' in window ||
    navigator.maxTouchPoints > 0 ||
    navigator.msMaxTouchPoints > 0
  );
};

/**
 * Detect if device is mobile (phones only, not tablets)
 * @returns {boolean} True if mobile phone
 */
export const isMobilePhone = () => {
  return /iPhone|Android.*Mobile|webOS|BlackBerry|IEMobile|Opera Mini/i.test(
    navigator.userAgent
  );
};

/**
 * Detect if device is tablet
 * @returns {boolean} True if tablet
 */
export const isTablet = () => {
  return /iPad|Android(?!.*Mobile)|Tablet|PlayBook/i.test(navigator.userAgent);
};

/**
 * Get current screen size category
 * @returns {string} Screen size category
 */
export const getScreenSize = () => {
  const width = window.innerWidth;

  if (width <= 375) return 'mobile-sm';
  if (width <= 667) return 'mobile-lg';
  if (width <= 1024) return 'tablet';
  if (width <= 1366) return 'tablet-lg';
  return 'desktop';
};

/**
 * Get device pixel ratio
 * @returns {number} Device pixel ratio
 */
export const getDevicePixelRatio = () => {
  return window.devicePixelRatio || 1;
};

/**
 * Detect iOS device
 * @returns {boolean} True if iOS
 */
export const isIOS = () => {
  return /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
};

/**
 * Detect Android device
 * @returns {boolean} True if Android
 */
export const isAndroid = () => {
  return /Android/i.test(navigator.userAgent);
};

/**
 * Add touch-friendly hover states to an element
 * Simulates hover on touchstart/touchend
 * @param {HTMLElement} element - Element to enhance
 * @param {string} activeClass - CSS class to add on touch (default: 'touch-active')
 */
export const addTouchHover = (element, activeClass = 'touch-active') => {
  if (!isTouchDevice() || !element) return;

  element.addEventListener('touchstart', () => {
    element.classList.add(activeClass);
  }, { passive: true });

  element.addEventListener('touchend', () => {
    setTimeout(() => {
      element.classList.remove(activeClass);
    }, 150);
  }, { passive: true });

  element.addEventListener('touchcancel', () => {
    element.classList.remove(activeClass);
  }, { passive: true });
};

/**
 * Prevent double-tap zoom on an element
 * Uses touch-action CSS property
 * @param {HTMLElement} element - Element to prevent zoom on
 */
export const preventDoubleTapZoom = (element) => {
  if (!element) return;

  element.style.touchAction = 'manipulation';
};

/**
 * Prevent pinch-to-zoom on an element
 * @param {HTMLElement} element - Element to prevent zoom on
 */
export const preventPinchZoom = (element) => {
  if (!element) return;

  element.style.touchAction = 'pan-x pan-y';
};

/**
 * Set mobile viewport meta tag to prevent zoom
 * Call once on app initialization
 */
export const setMobileViewport = () => {
  let viewport = document.querySelector('meta[name="viewport"]');

  if (!viewport) {
    viewport = document.createElement('meta');
    viewport.name = 'viewport';
    document.head.appendChild(viewport);
  }

  viewport.setAttribute(
    'content',
    'width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover'
  );
};

/**
 * Set mobile viewport to allow zoom (for accessibility)
 * Recommended for content-heavy pages
 */
export const setMobileViewportAccessible = () => {
  let viewport = document.querySelector('meta[name="viewport"]');

  if (!viewport) {
    viewport = document.createElement('meta');
    viewport.name = 'viewport';
    document.head.appendChild(viewport);
  }

  viewport.setAttribute(
    'content',
    'width=device-width, initial-scale=1.0, viewport-fit=cover'
  );
};

/**
 * Detect if element is visible in viewport
 * @param {HTMLElement} element - Element to check
 * @returns {boolean} True if visible
 */
export const isElementInViewport = (element) => {
  if (!element) return false;

  const rect = element.getBoundingClientRect();
  return (
    rect.top >= 0 &&
    rect.left >= 0 &&
    rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
    rect.right <= (window.innerWidth || document.documentElement.clientWidth)
  );
};

/**
 * Smooth scroll to element
 * @param {HTMLElement|string} elementOrSelector - Element or selector to scroll to
 * @param {object} options - Scroll options
 */
export const smoothScrollTo = (elementOrSelector, options = {}) => {
  const element = typeof elementOrSelector === 'string'
    ? document.querySelector(elementOrSelector)
    : elementOrSelector;

  if (!element) return;

  const defaultOptions = {
    behavior: 'smooth',
    block: 'start',
    inline: 'nearest',
    ...options
  };

  element.scrollIntoView(defaultOptions);
};

/**
 * Handle swipe gestures
 * @param {HTMLElement} element - Element to track swipes on
 * @param {object} callbacks - Callback functions for swipe directions
 * @returns {function} Cleanup function to remove listeners
 */
export const handleSwipe = (element, callbacks = {}) => {
  if (!element || !isTouchDevice()) return () => {};

  let touchStartX = 0;
  let touchStartY = 0;
  let touchEndX = 0;
  let touchEndY = 0;

  const minSwipeDistance = 50;

  const handleTouchStart = (e) => {
    touchStartX = e.changedTouches[0].screenX;
    touchStartY = e.changedTouches[0].screenY;
  };

  const handleTouchEnd = (e) => {
    touchEndX = e.changedTouches[0].screenX;
    touchEndY = e.changedTouches[0].screenY;

    const deltaX = touchEndX - touchStartX;
    const deltaY = touchEndY - touchStartY;

    // Determine swipe direction
    if (Math.abs(deltaX) > Math.abs(deltaY)) {
      // Horizontal swipe
      if (Math.abs(deltaX) > minSwipeDistance) {
        if (deltaX > 0 && callbacks.onSwipeRight) {
          callbacks.onSwipeRight(deltaX);
        } else if (deltaX < 0 && callbacks.onSwipeLeft) {
          callbacks.onSwipeLeft(Math.abs(deltaX));
        }
      }
    } else {
      // Vertical swipe
      if (Math.abs(deltaY) > minSwipeDistance) {
        if (deltaY > 0 && callbacks.onSwipeDown) {
          callbacks.onSwipeDown(deltaY);
        } else if (deltaY < 0 && callbacks.onSwipeUp) {
          callbacks.onSwipeUp(Math.abs(deltaY));
        }
      }
    }
  };

  element.addEventListener('touchstart', handleTouchStart, { passive: true });
  element.addEventListener('touchend', handleTouchEnd, { passive: true });

  // Return cleanup function
  return () => {
    element.removeEventListener('touchstart', handleTouchStart);
    element.removeEventListener('touchend', handleTouchEnd);
  };
};

/**
 * Debounce resize events for performance
 * @param {function} callback - Function to call on resize
 * @param {number} delay - Delay in milliseconds (default: 250)
 * @returns {function} Cleanup function to remove listener
 */
export const onResize = (callback, delay = 250) => {
  let timeoutId;

  const handleResize = () => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => {
      callback({
        width: window.innerWidth,
        height: window.innerHeight,
        screenSize: getScreenSize()
      });
    }, delay);
  };

  window.addEventListener('resize', handleResize);

  // Call immediately
  handleResize();

  // Return cleanup function
  return () => {
    clearTimeout(timeoutId);
    window.removeEventListener('resize', handleResize);
  };
};

/**
 * Detect orientation change
 * @param {function} callback - Function to call on orientation change
 * @returns {function} Cleanup function to remove listener
 */
export const onOrientationChange = (callback) => {
  const handleOrientationChange = () => {
    const orientation = window.innerWidth > window.innerHeight
      ? 'landscape'
      : 'portrait';

    callback({
      orientation,
      width: window.innerWidth,
      height: window.innerHeight
    });
  };

  window.addEventListener('orientationchange', handleOrientationChange);
  window.addEventListener('resize', handleOrientationChange);

  // Call immediately
  handleOrientationChange();

  // Return cleanup function
  return () => {
    window.removeEventListener('orientationchange', handleOrientationChange);
    window.removeEventListener('resize', handleOrientationChange);
  };
};

/**
 * Add ripple effect to button on touch
 * @param {HTMLElement} element - Button element
 */
export const addRippleEffect = (element) => {
  if (!element || !isTouchDevice()) return;

  element.classList.add('ripple');

  element.addEventListener('touchstart', (e) => {
    const ripple = document.createElement('span');
    const rect = element.getBoundingClientRect();
    const size = Math.max(rect.width, rect.height);
    const x = e.touches[0].clientX - rect.left - size / 2;
    const y = e.touches[0].clientY - rect.top - size / 2;

    ripple.style.width = ripple.style.height = `${size}px`;
    ripple.style.left = `${x}px`;
    ripple.style.top = `${y}px`;
    ripple.classList.add('ripple-effect');

    element.appendChild(ripple);

    setTimeout(() => {
      ripple.remove();
    }, 600);
  }, { passive: true });
};

/**
 * Optimize all touch targets on the page
 * Ensures minimum 44x44px touch target size
 * @param {HTMLElement} container - Container to optimize (default: document.body)
 */
export const optimizeTouchTargets = (container = document.body) => {
  if (!isTouchDevice()) return;

  const minSize = 44;
  const selectors = 'button, a, input, select, textarea, [role="button"]';
  const elements = container.querySelectorAll(selectors);

  elements.forEach(element => {
    const rect = element.getBoundingClientRect();

    if (rect.width < minSize || rect.height < minSize) {
      element.style.minWidth = `${minSize}px`;
      element.style.minHeight = `${minSize}px`;
    }

    // Prevent double-tap zoom on buttons
    if (element.tagName === 'BUTTON' || element.getAttribute('role') === 'button') {
      preventDoubleTapZoom(element);
    }
  });
};

/**
 * Initialize all touch optimizations
 * Call once on app mount
 * @param {object} options - Configuration options
 */
export const initTouchOptimizations = (options = {}) => {
  const defaults = {
    preventZoom: true,
    optimizeTargets: true,
    addHoverStates: true,
    enableRipple: false,
    ...options
  };

  if (!isTouchDevice()) return;

  // Set viewport
  if (defaults.preventZoom) {
    setMobileViewport();
  } else {
    setMobileViewportAccessible();
  }

  // Optimize touch targets
  if (defaults.optimizeTargets) {
    optimizeTouchTargets();
  }

  // Add touch hover states
  if (defaults.addHoverStates) {
    const interactiveElements = document.querySelectorAll(
      'button, a, [role="button"], .touch-target'
    );
    interactiveElements.forEach(element => addTouchHover(element));
  }

  // Add ripple effects
  if (defaults.enableRipple) {
    const buttons = document.querySelectorAll('button, [role="button"]');
    buttons.forEach(button => addRippleEffect(button));
  }

  console.log('Touch optimizations initialized', {
    device: isMobilePhone() ? 'mobile' : isTablet() ? 'tablet' : 'touch-device',
    screenSize: getScreenSize(),
    pixelRatio: getDevicePixelRatio()
  });
};

/**
 * Get safe area insets for notched devices
 * @returns {object} Safe area insets
 */
export const getSafeAreaInsets = () => {
  const style = getComputedStyle(document.documentElement);

  return {
    top: parseInt(style.getPropertyValue('env(safe-area-inset-top)') || 0),
    right: parseInt(style.getPropertyValue('env(safe-area-inset-right)') || 0),
    bottom: parseInt(style.getPropertyValue('env(safe-area-inset-bottom)') || 0),
    left: parseInt(style.getPropertyValue('env(safe-area-inset-left)') || 0)
  };
};

/**
 * Export all utilities as default
 */
export default {
  isTouchDevice,
  isMobilePhone,
  isTablet,
  isIOS,
  isAndroid,
  getScreenSize,
  getDevicePixelRatio,
  addTouchHover,
  preventDoubleTapZoom,
  preventPinchZoom,
  setMobileViewport,
  setMobileViewportAccessible,
  isElementInViewport,
  smoothScrollTo,
  handleSwipe,
  onResize,
  onOrientationChange,
  addRippleEffect,
  optimizeTouchTargets,
  initTouchOptimizations,
  getSafeAreaInsets
};
