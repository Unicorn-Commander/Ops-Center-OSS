/**
 * useTouchGestures Hook
 *
 * Custom hook for handling touch gestures (swipe, tap, long press)
 * Useful for mobile-friendly interactions
 *
 * @param {Object} callbacks - Gesture callbacks
 * @returns {Object} Touch event handlers
 */

import { useRef, useCallback } from 'react';

const SWIPE_THRESHOLD = 50; // Minimum distance for swipe (px)
const SWIPE_VELOCITY_THRESHOLD = 0.3; // Minimum velocity for swipe (px/ms)
const LONG_PRESS_DURATION = 500; // Duration for long press (ms)
const DOUBLE_TAP_DELAY = 300; // Maximum delay between taps (ms)

export const useTouchGestures = ({
  onSwipeLeft,
  onSwipeRight,
  onSwipeUp,
  onSwipeDown,
  onTap,
  onDoubleTap,
  onLongPress,
} = {}) => {
  const touchStartRef = useRef(null);
  const touchEndRef = useRef(null);
  const longPressTimerRef = useRef(null);
  const lastTapRef = useRef(null);
  const preventNextTapRef = useRef(false);

  const handleTouchStart = useCallback((e) => {
    const touch = e.touches[0];
    touchStartRef.current = {
      x: touch.clientX,
      y: touch.clientY,
      time: Date.now(),
    };
    touchEndRef.current = null;

    // Start long press timer
    if (onLongPress) {
      longPressTimerRef.current = setTimeout(() => {
        onLongPress(e);
        preventNextTapRef.current = true;
      }, LONG_PRESS_DURATION);
    }
  }, [onLongPress]);

  const handleTouchMove = useCallback((e) => {
    const touch = e.touches[0];
    touchEndRef.current = {
      x: touch.clientX,
      y: touch.clientY,
      time: Date.now(),
    };

    // Cancel long press if finger moves
    if (longPressTimerRef.current) {
      const deltaX = Math.abs(touchEndRef.current.x - touchStartRef.current.x);
      const deltaY = Math.abs(touchEndRef.current.y - touchStartRef.current.y);

      if (deltaX > 10 || deltaY > 10) {
        clearTimeout(longPressTimerRef.current);
        longPressTimerRef.current = null;
      }
    }
  }, []);

  const handleTouchEnd = useCallback((e) => {
    // Clear long press timer
    if (longPressTimerRef.current) {
      clearTimeout(longPressTimerRef.current);
      longPressTimerRef.current = null;
    }

    // Check if we should prevent tap
    if (preventNextTapRef.current) {
      preventNextTapRef.current = false;
      return;
    }

    if (!touchStartRef.current) return;

    const touchEnd = touchEndRef.current || {
      x: touchStartRef.current.x,
      y: touchStartRef.current.y,
      time: Date.now(),
    };

    const deltaX = touchEnd.x - touchStartRef.current.x;
    const deltaY = touchEnd.y - touchStartRef.current.y;
    const deltaTime = touchEnd.time - touchStartRef.current.time;

    const distanceX = Math.abs(deltaX);
    const distanceY = Math.abs(deltaY);
    const velocityX = distanceX / deltaTime;
    const velocityY = distanceY / deltaTime;

    // Detect swipe
    if (distanceX > SWIPE_THRESHOLD || distanceY > SWIPE_THRESHOLD) {
      if (velocityX > SWIPE_VELOCITY_THRESHOLD || velocityY > SWIPE_VELOCITY_THRESHOLD) {
        if (distanceX > distanceY) {
          // Horizontal swipe
          if (deltaX > 0 && onSwipeRight) {
            onSwipeRight(e, { distance: distanceX, velocity: velocityX });
          } else if (deltaX < 0 && onSwipeLeft) {
            onSwipeLeft(e, { distance: distanceX, velocity: velocityX });
          }
        } else {
          // Vertical swipe
          if (deltaY > 0 && onSwipeDown) {
            onSwipeDown(e, { distance: distanceY, velocity: velocityY });
          } else if (deltaY < 0 && onSwipeUp) {
            onSwipeUp(e, { distance: distanceY, velocity: velocityY });
          }
        }
        return; // Don't process as tap
      }
    }

    // Detect tap (no significant movement)
    if (distanceX < 10 && distanceY < 10) {
      const now = Date.now();

      // Check for double tap
      if (lastTapRef.current && now - lastTapRef.current < DOUBLE_TAP_DELAY) {
        if (onDoubleTap) {
          onDoubleTap(e);
          lastTapRef.current = null; // Reset after double tap
          return;
        }
      }

      // Single tap
      if (onTap) {
        onTap(e);
      }
      lastTapRef.current = now;
    }

    // Reset
    touchStartRef.current = null;
    touchEndRef.current = null;
  }, [onSwipeLeft, onSwipeRight, onSwipeUp, onSwipeDown, onTap, onDoubleTap]);

  return {
    onTouchStart: handleTouchStart,
    onTouchMove: handleTouchMove,
    onTouchEnd: handleTouchEnd,
  };
};

export default useTouchGestures;
