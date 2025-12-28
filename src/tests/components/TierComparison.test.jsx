/**
 * Epic 2.4: Self-Service Upgrades - Frontend Component Tests
 *
 * Comprehensive test suite for TierComparison and related upgrade UI components.
 *
 * Test Coverage:
 * - Tier card rendering
 * - Current tier highlighting
 * - Upgrade/downgrade button states
 * - Loading states
 * - Error handling
 * - User interactions
 * - Accessibility
 *
 * Author: Testing & UX Lead
 * Date: October 24, 2025
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import '@testing-library/jest-dom';
import TierComparison from '../../components/billing/TierComparison';
import UpgradeFlow from '../../components/billing/UpgradeFlow';
import DowngradeConfirmation from '../../components/billing/DowngradeConfirmation';

// Mock fetch
global.fetch = jest.fn();

// Mock navigate
const mockNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
}));

// Helper to render with router
const renderWithRouter = (component) => {
  return render(<BrowserRouter>{component}</BrowserRouter>);
};

// ============================================================================
// TIER COMPARISON COMPONENT TESTS
// ============================================================================

describe('TierComparison Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    fetch.mockClear();
  });

  // ------------------------------------------------------------------------
  // RENDERING TESTS
  // ------------------------------------------------------------------------

  test('renders all 4 tier cards', () => {
    renderWithRouter(<TierComparison currentTier="starter" />);

    expect(screen.getByText('Trial')).toBeInTheDocument();
    expect(screen.getByText('Starter')).toBeInTheDocument();
    expect(screen.getByText('Professional')).toBeInTheDocument();
    expect(screen.getByText('Enterprise')).toBeInTheDocument();
  });

  test('displays correct pricing for each tier', () => {
    renderWithRouter(<TierComparison currentTier="starter" />);

    expect(screen.getByText(/\$1\.00/)).toBeInTheDocument(); // Trial
    expect(screen.getByText(/\$19\.00/)).toBeInTheDocument(); // Starter
    expect(screen.getByText(/\$49\.00/)).toBeInTheDocument(); // Professional
    expect(screen.getByText(/\$99\.00/)).toBeInTheDocument(); // Enterprise
  });

  test('displays feature lists for each tier', () => {
    renderWithRouter(<TierComparison currentTier="starter" />);

    // Trial features
    expect(screen.getByText(/7-day trial/i)).toBeInTheDocument();
    expect(screen.getByText(/100 API calls\/day/i)).toBeInTheDocument();

    // Starter features
    expect(screen.getByText(/1,000 API calls\/month/i)).toBeInTheDocument();

    // Professional features
    expect(screen.getByText(/10,000 API calls\/month/i)).toBeInTheDocument();

    // Enterprise features
    expect(screen.getByText(/Unlimited API calls/i)).toBeInTheDocument();
  });

  test('highlights professional tier as "Most Popular"', () => {
    renderWithRouter(<TierComparison currentTier="starter" />);

    const professionalCard = screen.getByText('Professional').closest('.MuiCard-root');
    const badge = within(professionalCard).getByText(/Most Popular/i);

    expect(badge).toBeInTheDocument();
    expect(badge).toHaveClass('popular-badge'); // Or appropriate class
  });

  // ------------------------------------------------------------------------
  // CURRENT TIER HIGHLIGHTING
  // ------------------------------------------------------------------------

  test('highlights current tier with checkmark', () => {
    renderWithRouter(<TierComparison currentTier="starter" />);

    const starterCard = screen.getByText('Starter').closest('.MuiCard-root');
    expect(starterCard).toHaveClass('current-tier');

    // Look for checkmark icon or "Current Plan" text
    const checkmark = within(starterCard).getByText(/Current Plan/i);
    expect(checkmark).toBeInTheDocument();
  });

  test('marks trial tier as current', () => {
    renderWithRouter(<TierComparison currentTier="trial" />);

    const trialCard = screen.getByText('Trial').closest('.MuiCard-root');
    expect(trialCard).toHaveClass('current-tier');
  });

  test('marks professional tier as current', () => {
    renderWithRouter(<TierComparison currentTier="professional" />);

    const professionalCard = screen.getByText('Professional').closest('.MuiCard-root');
    expect(professionalCard).toHaveClass('current-tier');
  });

  // ------------------------------------------------------------------------
  // BUTTON STATE TESTS
  // ------------------------------------------------------------------------

  test('shows upgrade button for higher tiers', () => {
    renderWithRouter(<TierComparison currentTier="starter" />);

    // Professional is higher than Starter
    const professionalCard = screen.getByText('Professional').closest('.MuiCard-root');
    const upgradeButton = within(professionalCard).getByRole('button', { name: /Upgrade/i });

    expect(upgradeButton).toBeInTheDocument();
    expect(upgradeButton).not.toBeDisabled();
  });

  test('shows downgrade button for lower tiers', () => {
    renderWithRouter(<TierComparison currentTier="professional" />);

    // Starter is lower than Professional
    const starterCard = screen.getByText('Starter').closest('.MuiCard-root');
    const downgradeButton = within(starterCard).getByRole('button', { name: /Downgrade/i });

    expect(downgradeButton).toBeInTheDocument();
    expect(downgradeButton).not.toBeDisabled();
  });

  test('disables button for current tier', () => {
    renderWithRouter(<TierComparison currentTier="professional" />);

    const professionalCard = screen.getByText('Professional').closest('.MuiCard-root');
    const currentButton = within(professionalCard).getByRole('button');

    expect(currentButton).toBeDisabled();
    expect(currentButton).toHaveTextContent(/Current Plan/i);
  });

  test('shows "Contact Sales" for enterprise when on lower tier', () => {
    renderWithRouter(<TierComparison currentTier="starter" />);

    const enterpriseCard = screen.getByText('Enterprise').closest('.MuiCard-root');
    const contactButton = within(enterpriseCard).getByRole('button', { name: /Contact Sales/i });

    expect(contactButton).toBeInTheDocument();
  });

  // ------------------------------------------------------------------------
  // INTERACTION TESTS
  // ------------------------------------------------------------------------

  test('clicking upgrade button triggers upgrade flow', async () => {
    renderWithRouter(<TierComparison currentTier="starter" />);

    const professionalCard = screen.getByText('Professional').closest('.MuiCard-root');
    const upgradeButton = within(professionalCard).getByRole('button', { name: /Upgrade/i });

    fireEvent.click(upgradeButton);

    // Should navigate or open modal
    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith(expect.stringContaining('/upgrade'));
    });
  });

  test('clicking downgrade button shows confirmation dialog', async () => {
    renderWithRouter(<TierComparison currentTier="professional" />);

    const starterCard = screen.getByText('Starter').closest('.MuiCard-root');
    const downgradeButton = within(starterCard).getByRole('button', { name: /Downgrade/i });

    fireEvent.click(downgradeButton);

    // Should show confirmation modal
    await waitFor(() => {
      expect(screen.getByText(/Are you sure/i)).toBeInTheDocument();
      expect(screen.getByText(/downgrade/i)).toBeInTheDocument();
    });
  });

  // ------------------------------------------------------------------------
  // LOADING STATE TESTS
  // ------------------------------------------------------------------------

  test('shows loading skeleton while fetching tiers', () => {
    // Mock loading state
    renderWithRouter(<TierComparison currentTier="starter" isLoading={true} />);

    // Should show skeleton loaders or spinner
    expect(screen.getByTestId('tier-loading-skeleton')).toBeInTheDocument();
  });

  test('shows tier cards after loading completes', async () => {
    const { rerender } = renderWithRouter(
      <TierComparison currentTier="starter" isLoading={true} />
    );

    expect(screen.getByTestId('tier-loading-skeleton')).toBeInTheDocument();

    // Simulate loading complete
    rerender(<TierComparison currentTier="starter" isLoading={false} />);

    await waitFor(() => {
      expect(screen.queryByTestId('tier-loading-skeleton')).not.toBeInTheDocument();
      expect(screen.getByText('Starter')).toBeInTheDocument();
    });
  });

  // ------------------------------------------------------------------------
  // ERROR HANDLING TESTS
  // ------------------------------------------------------------------------

  test('shows error message when tier data fails to load', () => {
    renderWithRouter(
      <TierComparison currentTier="starter" error="Failed to load subscription plans" />
    );

    expect(screen.getByText(/Failed to load/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Retry/i })).toBeInTheDocument();
  });

  test('retry button refetches tier data', async () => {
    const mockRefetch = jest.fn();

    renderWithRouter(
      <TierComparison
        currentTier="starter"
        error="Failed to load subscription plans"
        onRetry={mockRefetch}
      />
    );

    const retryButton = screen.getByRole('button', { name: /Retry/i });
    fireEvent.click(retryButton);

    expect(mockRefetch).toHaveBeenCalledTimes(1);
  });
});

// ============================================================================
// UPGRADE FLOW COMPONENT TESTS
// ============================================================================

describe('UpgradeFlow Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    fetch.mockClear();
  });

  // ------------------------------------------------------------------------
  // STEPPER TESTS
  // ------------------------------------------------------------------------

  test('shows stepper with 3 steps', () => {
    renderWithRouter(<UpgradeFlow targetTier="professional" currentTier="starter" />);

    expect(screen.getByText(/Step 1/i)).toBeInTheDocument();
    expect(screen.getByText(/Step 2/i)).toBeInTheDocument();
    expect(screen.getByText(/Step 3/i)).toBeInTheDocument();
  });

  test('step 1 shows tier comparison', () => {
    renderWithRouter(<UpgradeFlow targetTier="professional" currentTier="starter" />);

    // Should show current and target tier details
    expect(screen.getByText(/Current: Starter/i)).toBeInTheDocument();
    expect(screen.getByText(/New: Professional/i)).toBeInTheDocument();
  });

  test('step 2 shows proration preview', async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        old_tier: 'starter',
        new_tier: 'professional',
        proration_amount: 39.50,
        credit_amount: 9.50,
        immediate_charge: 39.50,
      }),
    });

    renderWithRouter(<UpgradeFlow targetTier="professional" currentTier="starter" />);

    // Click next to go to step 2
    const nextButton = screen.getByRole('button', { name: /Next/i });
    fireEvent.click(nextButton);

    await waitFor(() => {
      expect(screen.getByText(/\$39\.50/)).toBeInTheDocument();
      expect(screen.getByText(/Credit: \$9\.50/i)).toBeInTheDocument();
    });
  });

  test('step 3 shows payment confirmation', async () => {
    renderWithRouter(<UpgradeFlow targetTier="professional" currentTier="starter" />);

    // Navigate to step 3
    const nextButton = screen.getByRole('button', { name: /Next/i });
    fireEvent.click(nextButton);
    fireEvent.click(nextButton);

    await waitFor(() => {
      expect(screen.getByText(/Confirm Payment/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Confirm/i })).toBeInTheDocument();
    });
  });

  // ------------------------------------------------------------------------
  // NAVIGATION TESTS
  // ------------------------------------------------------------------------

  test('can navigate forward through steps', async () => {
    renderWithRouter(<UpgradeFlow targetTier="professional" currentTier="starter" />);

    const nextButton = screen.getByRole('button', { name: /Next/i });

    // Start at step 1
    expect(screen.getByText(/Step 1/i)).toHaveClass('active');

    // Go to step 2
    fireEvent.click(nextButton);
    await waitFor(() => {
      expect(screen.getByText(/Step 2/i)).toHaveClass('active');
    });

    // Go to step 3
    fireEvent.click(nextButton);
    await waitFor(() => {
      expect(screen.getByText(/Step 3/i)).toHaveClass('active');
    });
  });

  test('can navigate backward through steps', async () => {
    renderWithRouter(<UpgradeFlow targetTier="professional" currentTier="starter" />);

    // Go forward to step 2
    const nextButton = screen.getByRole('button', { name: /Next/i });
    fireEvent.click(nextButton);

    await waitFor(() => {
      expect(screen.getByText(/Step 2/i)).toHaveClass('active');
    });

    // Go back to step 1
    const backButton = screen.getByRole('button', { name: /Back/i });
    fireEvent.click(backButton);

    await waitFor(() => {
      expect(screen.getByText(/Step 1/i)).toHaveClass('active');
    });
  });

  // ------------------------------------------------------------------------
  // PAYMENT CONFIRMATION TESTS
  // ------------------------------------------------------------------------

  test('confirm button initiates Stripe checkout', async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        checkout_url: 'https://checkout.stripe.com/session_xxx',
        session_id: 'cs_test_xxx',
      }),
    });

    renderWithRouter(<UpgradeFlow targetTier="professional" currentTier="starter" />);

    // Navigate to step 3
    const nextButton = screen.getByRole('button', { name: /Next/i });
    fireEvent.click(nextButton);
    fireEvent.click(nextButton);

    await waitFor(() => {
      const confirmButton = screen.getByRole('button', { name: /Confirm/i });
      fireEvent.click(confirmButton);
    });

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/subscriptions/upgrade'),
        expect.objectContaining({
          method: 'POST',
          body: expect.stringContaining('professional'),
        })
      );
    });
  });

  test('shows loading state during payment processing', async () => {
    fetch.mockImplementationOnce(
      () => new Promise((resolve) => setTimeout(() => resolve({ ok: true, json: async () => ({}) }), 2000))
    );

    renderWithRouter(<UpgradeFlow targetTier="professional" currentTier="starter" />);

    // Navigate to step 3 and click confirm
    const nextButton = screen.getByRole('button', { name: /Next/i });
    fireEvent.click(nextButton);
    fireEvent.click(nextButton);

    await waitFor(() => {
      const confirmButton = screen.getByRole('button', { name: /Confirm/i });
      fireEvent.click(confirmButton);
    });

    // Should show loading state
    expect(screen.getByText(/Processing/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Confirm/i })).toBeDisabled();
  });

  // ------------------------------------------------------------------------
  // ERROR HANDLING TESTS
  // ------------------------------------------------------------------------

  test('shows error message when API call fails', async () => {
    fetch.mockRejectedValueOnce(new Error('Network error'));

    renderWithRouter(<UpgradeFlow targetTier="professional" currentTier="starter" />);

    // Navigate to step 3 and click confirm
    const nextButton = screen.getByRole('button', { name: /Next/i });
    fireEvent.click(nextButton);
    fireEvent.click(nextButton);

    await waitFor(() => {
      const confirmButton = screen.getByRole('button', { name: /Confirm/i });
      fireEvent.click(confirmButton);
    });

    await waitFor(() => {
      expect(screen.getByText(/Error/i)).toBeInTheDocument();
      expect(screen.getByText(/Network error/i)).toBeInTheDocument();
    });
  });

  test('allows retry after error', async () => {
    fetch
      .mockRejectedValueOnce(new Error('Network error'))
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          checkout_url: 'https://checkout.stripe.com/session_xxx',
        }),
      });

    renderWithRouter(<UpgradeFlow targetTier="professional" currentTier="starter" />);

    // Navigate to step 3 and trigger error
    const nextButton = screen.getByRole('button', { name: /Next/i });
    fireEvent.click(nextButton);
    fireEvent.click(nextButton);

    await waitFor(() => {
      const confirmButton = screen.getByRole('button', { name: /Confirm/i });
      fireEvent.click(confirmButton);
    });

    await waitFor(() => {
      expect(screen.getByText(/Network error/i)).toBeInTheDocument();
    });

    // Click retry
    const retryButton = screen.getByRole('button', { name: /Retry/i });
    fireEvent.click(retryButton);

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledTimes(2);
    });
  });
});

// ============================================================================
// DOWNGRADE CONFIRMATION COMPONENT TESTS
// ============================================================================

describe('DowngradeConfirmation Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('shows warning about downgrade timing', () => {
    renderWithRouter(
      <DowngradeConfirmation
        currentTier="professional"
        targetTier="starter"
        effectiveDate="2025-11-24"
      />
    );

    expect(screen.getByText(/end of billing period/i)).toBeInTheDocument();
    expect(screen.getByText(/November 24, 2025/i)).toBeInTheDocument();
  });

  test('shows feature comparison (what user will lose)', () => {
    renderWithRouter(
      <DowngradeConfirmation currentTier="professional" targetTier="starter" />
    );

    expect(screen.getByText(/You will lose access to:/i)).toBeInTheDocument();
    expect(screen.getByText(/10,000 API calls/i)).toBeInTheDocument();
    expect(screen.getByText(/Priority support/i)).toBeInTheDocument();
  });

  test('requires confirmation checkbox before allowing downgrade', () => {
    renderWithRouter(
      <DowngradeConfirmation currentTier="professional" targetTier="starter" />
    );

    const confirmButton = screen.getByRole('button', { name: /Confirm Downgrade/i });

    // Initially disabled
    expect(confirmButton).toBeDisabled();

    // Enable after checking checkbox
    const checkbox = screen.getByRole('checkbox', { name: /I understand/i });
    fireEvent.click(checkbox);

    expect(confirmButton).not.toBeDisabled();
  });

  test('cancel button closes modal', () => {
    const mockClose = jest.fn();

    renderWithRouter(
      <DowngradeConfirmation
        currentTier="professional"
        targetTier="starter"
        onClose={mockClose}
      />
    );

    const cancelButton = screen.getByRole('button', { name: /Cancel/i });
    fireEvent.click(cancelButton);

    expect(mockClose).toHaveBeenCalledTimes(1);
  });
});

// ============================================================================
// ACCESSIBILITY TESTS
// ============================================================================

describe('Accessibility', () => {
  test('tier cards have proper aria labels', () => {
    renderWithRouter(<TierComparison currentTier="starter" />);

    const professionalCard = screen.getByLabelText(/Professional tier/i);
    expect(professionalCard).toBeInTheDocument();
  });

  test('buttons have descriptive aria labels', () => {
    renderWithRouter(<TierComparison currentTier="starter" />);

    const upgradeButton = screen.getByLabelText(/Upgrade to Professional/i);
    expect(upgradeButton).toBeInTheDocument();
  });

  test('keyboard navigation works through stepper', async () => {
    renderWithRouter(<UpgradeFlow targetTier="professional" currentTier="starter" />);

    const nextButton = screen.getByRole('button', { name: /Next/i });

    // Tab to button
    nextButton.focus();
    expect(nextButton).toHaveFocus();

    // Press Enter
    fireEvent.keyDown(nextButton, { key: 'Enter', code: 'Enter' });

    await waitFor(() => {
      expect(screen.getByText(/Step 2/i)).toHaveClass('active');
    });
  });

  test('screen reader announcements for step changes', async () => {
    renderWithRouter(<UpgradeFlow targetTier="professional" currentTier="starter" />);

    const announcement = screen.getByRole('status', { hidden: true });

    const nextButton = screen.getByRole('button', { name: /Next/i });
    fireEvent.click(nextButton);

    await waitFor(() => {
      expect(announcement).toHaveTextContent(/Step 2 of 3/i);
    });
  });
});
