/**
 * useSwipeGestures Hook - Touch Gesture Detection
 *
 * Detects left/right swipe gestures for mobile navigation
 * Minimum swipe distance: 50px
 *
 * @param {Function} onSwipeLeft - Callback for left swipe
 * @param {Function} onSwipeRight - Callback for right swipe
 * @returns {Object} Touch event handlers
 */

import { useState, useCallback, useRef } from 'react';

export function useSwipeGestures(onSwipeLeft, onSwipeRight) {
  const [touchStart, setTouchStart] = useState(null);
  const [touchEnd, setTouchEnd] = useState(null);
  const touchStartTime = useRef(null);

  // Minimum swipe distance (in pixels)
  const minSwipeDistance = 50;

  // Maximum swipe time (in milliseconds) - prevents slow drags
  const maxSwipeTime = 500;

  // Maximum vertical movement allowed for horizontal swipe
  const maxVerticalDeviation = 100;

  const onTouchStart = useCallback((e) => {
    setTouchEnd(null);
    setTouchStart({
      x: e.targetTouches[0].clientX,
      y: e.targetTouches[0].clientY
    });
    touchStartTime.current = Date.now();
  }, []);

  const onTouchMove = useCallback((e) => {
    setTouchEnd({
      x: e.targetTouches[0].clientX,
      y: e.targetTouches[0].clientY
    });
  }, []);

  const onTouchEnd = useCallback(() => {
    if (!touchStart || !touchEnd) return;

    const swipeTime = Date.now() - touchStartTime.current;
    const distanceX = touchStart.x - touchEnd.x;
    const distanceY = Math.abs(touchStart.y - touchEnd.y);

    // Check if swipe was fast enough and horizontal enough
    if (swipeTime > maxSwipeTime) return;
    if (distanceY > maxVerticalDeviation) return;

    const isLeftSwipe = distanceX > minSwipeDistance;
    const isRightSwipe = distanceX < -minSwipeDistance;

    if (isLeftSwipe && onSwipeLeft) {
      onSwipeLeft();
    }

    if (isRightSwipe && onSwipeRight) {
      onSwipeRight();
    }

    // Reset state
    setTouchStart(null);
    setTouchEnd(null);
    touchStartTime.current = null;
  }, [touchStart, touchEnd, onSwipeLeft, onSwipeRight]);

  return {
    onTouchStart,
    onTouchMove,
    onTouchEnd
  };
}

/**
 * useSwipeDrawer Hook - Swipe-to-Open Drawer Functionality
 *
 * Manages drawer state with swipe gestures
 * Swipe right from edge: Open drawer
 * Swipe left while open: Close drawer
 *
 * @param {boolean} initialOpen - Initial drawer state
 * @returns {Object} Drawer state and handlers
 */
export function useSwipeDrawer(initialOpen = false) {
  const [isOpen, setIsOpen] = useState(initialOpen);
  const [edgeSwipeEnabled, setEdgeSwipeEnabled] = useState(true);

  // Edge detection zone (pixels from left edge)
  const edgeZoneWidth = 20;

  const handleSwipeRight = useCallback(() => {
    if (!isOpen) {
      setIsOpen(true);
    }
  }, [isOpen]);

  const handleSwipeLeft = useCallback(() => {
    if (isOpen) {
      setIsOpen(false);
    }
  }, [isOpen]);

  const swipeHandlers = useSwipeGestures(handleSwipeLeft, handleSwipeRight);

  const onTouchStartWithEdge = useCallback((e) => {
    // Only allow swipe-to-open if touch starts near left edge
    const touchX = e.targetTouches[0].clientX;

    if (!isOpen && touchX > edgeZoneWidth) {
      // Disable swipe if not near edge
      return;
    }

    swipeHandlers.onTouchStart(e);
  }, [isOpen, swipeHandlers]);

  return {
    isOpen,
    setIsOpen,
    swipeHandlers: {
      ...swipeHandlers,
      onTouchStart: onTouchStartWithEdge
    },
    toggleDrawer: () => setIsOpen(prev => !prev),
    openDrawer: () => setIsOpen(true),
    closeDrawer: () => setIsOpen(false),
    edgeSwipeEnabled,
    setEdgeSwipeEnabled
  };
}
