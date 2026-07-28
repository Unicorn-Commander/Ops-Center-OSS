import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

const PRODUCT_TIERS = ['free', 'app', 'byok', 'managed'];

const formatPrice = (value) => {
  const amount = Number(value || 0);
  return amount === 0 ? 'Free' : `$${amount.toFixed(0)}`;
};

const signupUrl = (tierCode) => {
  const destination = tierCode === 'free'
    ? '/dashboard'
    : `/checkout/continue?tier=${encodeURIComponent(tierCode)}`;
  return `/auth/login?signup=1&return_url=${encodeURIComponent(destination)}`;
};

export default function MarketplaceLanding() {
  const [tiers, setTiers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [startingTier, setStartingTier] = useState(null);

  useEffect(() => {
    const loadTiers = async () => {
      try {
        const response = await fetch('/api/v1/public/pricing/tiers?include_features=true');
        if (!response.ok) throw new Error('Pricing is temporarily unavailable.');
        const data = await response.json();
        setTiers(
          PRODUCT_TIERS
            .map((code) => data.find((tier) => tier.tier_code === code))
            .filter(Boolean)
        );
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    loadTiers();
  }, []);

  const selectTier = async (tier) => {
    if (tier.tier_code === 'free') {
      window.location.href = signupUrl('free');
      return;
    }

    setStartingTier(tier.tier_code);
    try {
      const sessionResponse = await fetch('/api/v1/auth/session', { credentials: 'include' });
      if (!sessionResponse.ok) {
        window.location.href = signupUrl(tier.tier_code);
        return;
      }
      const checkoutResponse = await fetch('/api/v1/billing/subscriptions/checkout', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tier_id: tier.tier_code, billing_cycle: 'monthly' })
      });
      const checkout = await checkoutResponse.json().catch(() => ({}));
      if (!checkoutResponse.ok) {
        throw new Error(checkout.detail || 'Unable to start checkout.');
      }
      window.location.href = checkout.checkout_url;
    } catch (err) {
      setError(err.message);
      setStartingTier(null);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-purple-950 to-slate-950 text-white">
      <header className="border-b border-purple-500/20 bg-slate-950/80 backdrop-blur">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6">
          <Link to="/" className="flex items-center gap-3 font-bold">
            <img src="/logos/The_Colonel.png" alt="" className="h-10 w-10 rounded-full" />
            Unicorn Commander
          </Link>
          <a href="/auth/login" className="rounded-lg border border-purple-400/60 px-5 py-2 font-medium hover:bg-purple-500/10">
            Sign in
          </a>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-4 py-16 sm:px-6">
        <section className="mx-auto max-w-3xl text-center">
          <p className="mb-4 text-sm font-semibold uppercase tracking-[0.25em] text-purple-300">AI operations suite</p>
          <h1 className="text-4xl font-bold sm:text-6xl">Choose the setup that fits your work</h1>
          <p className="mt-6 text-lg text-slate-300">
            Start free with on-device meeting AI, or unlock Meeting-Ops for full server-side processing. More Ops apps rolling out soon.
          </p>
        </section>

        <section id="pricing" className="mt-14">
          {error && (
            <div role="alert" className="mx-auto mb-6 max-w-2xl rounded-lg border border-red-400/40 bg-red-950/40 p-4 text-red-200">
              {error}
            </div>
          )}

          {loading ? (
            <div className="py-20 text-center text-slate-300">Loading current plans…</div>
          ) : (
            <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-4">
              {tiers.map((tier) => {
                const paid = Number(tier.monthly_price_usd) > 0;
                const checkoutReady = !paid || tier.stripe_price_monthly_configured;
                const busy = startingTier === tier.tier_code;
                return (
                  <article
                    key={tier.tier_code}
                    className={`flex min-h-[430px] flex-col rounded-2xl border p-6 ${
                      tier.is_popular
                        ? 'border-purple-400 bg-purple-500/15 shadow-xl shadow-purple-950/40'
                        : 'border-slate-700 bg-slate-900/70'
                    }`}
                  >
                    {tier.badge_text && (
                      <span className="mb-4 w-fit rounded-full bg-purple-500 px-3 py-1 text-xs font-semibold">
                        {tier.badge_text}
                      </span>
                    )}
                    <h2 className="text-2xl font-semibold">{tier.display_name || tier.tier_name}</h2>
                    <p className="mt-2 min-h-16 text-sm text-slate-300">{tier.description}</p>
                    <p className="mt-5 text-4xl font-bold text-purple-300">
                      {formatPrice(tier.monthly_price_usd)}
                      {paid && <span className="text-base font-normal text-slate-400">/month</span>}
                    </p>
                    <ul className="mt-6 flex-1 space-y-3 text-sm text-slate-200">
                      {(tier.features || []).slice(0, 6).map((feature) => (
                        <li key={feature} className="flex gap-2">
                          <span className="text-emerald-400">✓</span>
                          <span>{feature}</span>
                        </li>
                      ))}
                    </ul>
                    <button
                      type="button"
                      disabled={!checkoutReady || busy}
                      onClick={() => selectTier(tier)}
                      className="mt-6 rounded-lg bg-purple-600 px-5 py-3 font-semibold hover:bg-purple-500 disabled:cursor-not-allowed disabled:bg-slate-700 disabled:text-slate-400"
                    >
                      {busy
                        ? 'Starting checkout…'
                        : !checkoutReady
                          ? 'Contact us'
                          : paid
                            ? 'Choose plan'
                            : 'Start free'}
                    </button>
                  </article>
                );
              })}
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
