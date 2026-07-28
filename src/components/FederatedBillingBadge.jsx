import React from 'react';
import { Box, Chip, Link, Tooltip, Typography } from '@mui/material';
import OpenInNewIcon from '@mui/icons-material/OpenInNew';
import ProvenanceBadge from './ProvenanceBadge';

/**
 * FederatedBillingBadge — provenance for the PLUGGABLE billing/metering function.
 *
 * Ops-Center is the single pane of glass; billing/metering can be operated locally
 * (this node charges) or FEDERATED to a central hub (Unicorn Commander). This badge
 * makes that transparent on billing screens: an admin still sees THIS node's own
 * billing numbers, but clearly understands the billing FUNCTION is provided by the
 * federated hub — with its logo, name, and a link home.
 *
 * Reads the same per-deployment config as ProvenanceBadge (useBillingConfig →
 * /api/v1/billing/provider-config). When provider !== 'federated' it preserves the
 * existing compact treatment (the ProvenanceBadge chip), so local/disabled nodes are
 * unchanged. Same code on every deployment; only env (BILLING_PROVIDER) changes.
 *
 * Props:
 *   config   — billing provider config from useBillingConfig()
 *   variant  — 'chip' (compact, sits next to a page title) | 'note' (a footer banner)
 *   prefix   — label prefix passed through to the non-federated ProvenanceBadge chip
 *   sx       — style overrides on the root
 */
export default function FederatedBillingBadge({ config, variant = 'chip', prefix = 'Billing', sx }) {
  if (!config) return null;

  const federated = config.provider === 'federated' || config?.source?.kind === 'remote';

  // Not federated → keep the existing behavior (compact provenance chip / nothing).
  if (!federated) {
    return <ProvenanceBadge config={config} prefix={prefix} sx={sx} />;
  }

  const name = config.provider_display_name || config.display_name || 'Unicorn Commander';
  const url = config.provider_url || config.manage_url || 'https://unicorncommander.ai';
  const logo = config.provider_logo_url || '/logos/uc-logo-512.png';
  const host = (url || '').replace(/^https?:\/\//, '').replace(/\/$/, '');

  const Logo = (
    <Box
      component="img"
      src={logo}
      alt={`${name} logo`}
      onError={(e) => { e.currentTarget.style.display = 'none'; }}
      sx={{ width: 18, height: 18, borderRadius: '4px', objectFit: 'contain', flexShrink: 0 }}
    />
  );

  // Compact chip — sits inline next to a page title.
  if (variant === 'chip') {
    return (
      <Tooltip
        arrow
        placement="bottom-start"
        title={`Billing & metering for this deployment is operated by ${name} (federated). This console shows your own numbers; the billing function lives at the hub.`}
      >
        <Chip
          size="small"
          variant="outlined"
          clickable
          component="a"
          href={url}
          target="_blank"
          rel="noopener noreferrer"
          icon={Logo}
          label={
            <Box component="span" sx={{ display: 'inline-flex', alignItems: 'center', gap: 0.5 }}>
              {`Billing by ${name}`}
              <OpenInNewIcon sx={{ fontSize: 13, opacity: 0.7 }} />
            </Box>
          }
          sx={{
            height: 24,
            fontSize: 11.5,
            fontWeight: 500,
            letterSpacing: 0.2,
            color: 'text.secondary',
            borderColor: 'rgba(160,170,210,0.22)',
            background: 'rgba(160,170,210,0.05)',
            cursor: 'pointer',
            '& .MuiChip-icon': { ml: 0.75, mr: -0.25 },
            ...sx,
          }}
        />
      </Tooltip>
    );
  }

  // Footer note — a subtle banner that spells out the federation relationship.
  return (
    <Box
      sx={{
        display: 'flex',
        alignItems: 'center',
        gap: 1.25,
        px: 1.5,
        py: 1,
        borderRadius: '12px',
        border: '1px solid rgba(160,170,210,0.18)',
        background: 'rgba(160,170,210,0.04)',
        ...sx,
      }}
    >
      {Logo}
      <Typography variant="caption" color="text.secondary" sx={{ lineHeight: 1.4 }}>
        Billing &amp; metering operated by{' '}
        <Box component="span" sx={{ fontWeight: 600, color: 'text.primary' }}>{name}</Box>
        {' '}— this console shows your portion;{' '}
        <Link
          href={url}
          target="_blank"
          rel="noopener noreferrer"
          underline="hover"
          sx={{ display: 'inline-flex', alignItems: 'center', gap: 0.25, color: 'inherit', fontWeight: 600 }}
        >
          {host || 'unicorncommander.ai'}
          <OpenInNewIcon sx={{ fontSize: 12 }} />
        </Link>
      </Typography>
    </Box>
  );
}
