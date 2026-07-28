import React, { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';

export default function CheckoutContinue() {
  const [searchParams] = useSearchParams();
  const [message, setMessage] = useState('Preparing secure checkout…');
  const tier = searchParams.get('tier');

  useEffect(() => {
    const continueCheckout = async () => {
      if (!tier) {
        setMessage('No plan was selected. Return to pricing and choose a plan.');
        return;
      }
      try {
        const sessionResponse = await fetch('/api/v1/auth/session', { credentials: 'include' });
        if (!sessionResponse.ok) {
          const returnUrl = `/checkout/continue?tier=${encodeURIComponent(tier)}`;
          window.location.replace(`/auth/login?signup=1&return_url=${encodeURIComponent(returnUrl)}`);
          return;
        }
        const response = await fetch('/api/v1/billing/subscriptions/checkout', {
          method: 'POST',
          credentials: 'include',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ tier_id: tier, billing_cycle: 'monthly' })
        });
        const data = await response.json().catch(() => ({}));
        if (!response.ok || !data.checkout_url) {
          throw new Error(data.detail || 'Unable to start checkout.');
        }
        window.location.replace(data.checkout_url);
      } catch (err) {
        setMessage(err.message);
      }
    };
    continueCheckout();
  }, [tier]);

  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-950 p-6 text-white">
      <div className="max-w-lg rounded-2xl border border-purple-500/30 bg-slate-900 p-8 text-center">
        <div className="mx-auto mb-5 h-10 w-10 animate-spin rounded-full border-4 border-purple-400 border-t-transparent" />
        <h1 className="text-2xl font-semibold">Finishing signup</h1>
        <p className="mt-3 text-slate-300">{message}</p>
        <a href="/pricing" className="mt-6 inline-block text-purple-300 hover:text-purple-200">
          Back to pricing
        </a>
      </div>
    </main>
  );
}
