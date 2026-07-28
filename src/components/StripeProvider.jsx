/**
 * Stripe Provider Wrapper
 * Provides Stripe.js context to the application
 */

import React, { useMemo } from 'react';
import { loadStripe } from '@stripe/stripe-js';
import { Elements } from '@stripe/react-stripe-js';

// Load Stripe publishable key from environment
const STRIPE_PUBLISHABLE_KEY = import.meta.env.VITE_STRIPE_PUBLISHABLE_KEY;

/**
 * StripeProvider Component
 *
 * Wraps children with Stripe Elements provider for payment processing
 */
export const StripeProvider = ({ children, publishableKey }) => {
  // Prefer a RUNTIME key (from /api/v1/billing/provider-config, passed in by the
  // page) so a deployment can enable card entry by setting STRIPE_PUBLISHABLE_KEY
  // on the backend — no frontend rebuild needed. Fall back to the build-time var.
  // Publishable keys are public by design, so this is safe.
  const key = publishableKey || STRIPE_PUBLISHABLE_KEY || null;

  // Memoize stripe promise to avoid recreating on every render
  const stripePromise = useMemo(() => {
    if (!key) {
      console.warn('Stripe publishable key not configured — card entry disabled, screen still renders.');
      return null;
    }
    return loadStripe(key);
  }, [key]);

  // ALWAYS provide an Elements context. When Stripe is unconfigured, stripePromise
  // is null — <Elements stripe={null}> is valid (Stripe's documented "loading"
  // state) and useStripe() returns null instead of throwing "Could not find
  // Elements context". Children guard on a null stripe (the add-card button stays
  // disabled). This keeps the Payment Methods screen rendering, never crashing.
  if (!stripePromise) {
    console.warn('Stripe not configured (VITE_STRIPE_PUBLISHABLE_KEY missing) — card entry disabled, screen still renders.');
  }

  return (
    <Elements stripe={stripePromise}>
      {children}
    </Elements>
  );
};

export default StripeProvider;
