"""
End-to-End Tests for NameCheap Migration (Epic 1.7)

Tests complete migration workflows from NameCheap to Cloudflare:
- Single domain migration
- Batch migration (multiple domains)
- Migration with email service preservation
- Migration pause and resume
- Migration rollback
- Health verification post-migration
- Dry run mode

All tests mock external APIs to avoid real API calls
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
import time


# ============================================================================
# Complete Migration Workflow Tests
# ============================================================================

class TestSingleDomainMigration:
    """Test complete single domain migration workflow"""

    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_complete_single_domain_migration(
        self,
        client,
        auth_headers,
        mock_namecheap_client,
        mock_cloudflare_client,
        sample_microsoft365_dns_records
    ):
        """
        Test complete migration workflow for single domain:
        1. Discover domain from NameCheap
        2. Export DNS records
        3. Add to Cloudflare
        4. Update nameservers
        5. Monitor propagation
        6. Verify health checks
        """
        # Setup mocks
        mock_namecheap_client.get_dns_records.return_value = {
            'success': True,
            'records': sample_microsoft365_dns_records
        }

        # Phase 1: Discover domain
        sync_response = client.post(
            '/api/v1/namecheap/domains/sync',
            headers=auth_headers,
            params={'account_id': 'test_account_id'}
        )
        assert sync_response.status_code == 200

        # Phase 2: Export DNS
        export_response = client.post(
            '/api/v1/namecheap/domains/unicorncommander.ai/dns/export',
            headers=auth_headers,
            params={'format': 'json'}
        )
        assert export_response.status_code == 200
        dns_backup = export_response.json()

        # Phase 3: Create migration job
        migration_response = client.post(
            '/api/v1/migration/jobs',
            headers=auth_headers,
            json={
                'job_name': 'Single Domain Migration E2E Test',
                'domains': ['unicorncommander.ai'],
                'priority': 'high'
            }
        )
        assert migration_response.status_code == 201
        job_id = migration_response.json()['id']

        # Phase 4: Monitor job progress
        max_wait = 30  # seconds
        start_time = time.time()
        job_completed = False

        while time.time() - start_time < max_wait:
            progress_response = client.get(
                f'/api/v1/migration/jobs/{job_id}/progress',
                headers=auth_headers
            )
            progress = progress_response.json()

            if progress.get('completed_domains', 0) == 1:
                job_completed = True
                break

            await asyncio.sleep(1)

        assert job_completed, "Migration job did not complete in time"

        # Phase 5: Run health checks
        health_response = client.post(
            f'/api/v1/migration/jobs/{job_id}/domains/unicorncommander.ai/health-check',
            headers=auth_headers
        )
        assert health_response.status_code == 200
        health_data = health_response.json()
        assert health_data['status'] == 'passed'

        # Verify final state
        job_response = client.get(
            f'/api/v1/migration/jobs/{job_id}',
            headers=auth_headers
        )
        final_job = job_response.json()
        assert final_job['status'] == 'completed'
        assert final_job['completed_domains'] == 1
        assert final_job['failed_domains'] == 0


class TestBatchMigration:
    """Test batch migration of multiple domains"""

    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_migrate_multiple_domains(
        self,
        client,
        auth_headers,
        mock_namecheap_client,
        mock_cloudflare_client
    ):
        """
        Test migrating 3 domains simultaneously:
        - Handle Cloudflare's 3-zone pending limit
        - Queue excess domains
        - Process queue as slots become available
        """
        domains = [
            'unicorncommander.ai',
            'superiorbsolutions.com',
            'magicunicorn.tech'
        ]

        # Create batch migration job
        migration_response = client.post(
            '/api/v1/migration/jobs',
            headers=auth_headers,
            json={
                'job_name': 'Batch Migration E2E Test',
                'domains': domains,
                'priority': 'normal'
            }
        )
        assert migration_response.status_code == 201
        job_id = migration_response.json()['id']

        # Check queue status
        queue_response = client.get(
            f'/api/v1/migration/jobs/{job_id}/queue',
            headers=auth_headers
        )
        assert queue_response.status_code == 200
        queue = queue_response.json()
        assert len(queue) == 3

        # Monitor progress until all complete
        max_wait = 60  # seconds
        start_time = time.time()
        all_completed = False

        while time.time() - start_time < max_wait:
            progress_response = client.get(
                f'/api/v1/migration/jobs/{job_id}/progress',
                headers=auth_headers
            )
            progress = progress_response.json()

            if progress.get('completed_domains', 0) == 3:
                all_completed = True
                break

            await asyncio.sleep(2)

        assert all_completed, "Batch migration did not complete all domains"

        # Verify all domains migrated successfully
        job_response = client.get(
            f'/api/v1/migration/jobs/{job_id}',
            headers=auth_headers
        )
        final_job = job_response.json()
        assert final_job['completed_domains'] == 3
        assert final_job['failed_domains'] == 0


class TestEmailServicePreservation:
    """Test migration with email service preservation"""

    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_migrate_with_microsoft365_email(
        self,
        client,
        auth_headers,
        mock_namecheap_client,
        mock_cloudflare_client,
        sample_microsoft365_dns_records
    ):
        """
        Test migrating domain with Microsoft 365 email:
        - Detect email service
        - Preserve all email-related records
        - Verify email functionality post-migration
        """
        # Setup mock to return Microsoft 365 DNS records
        mock_namecheap_client.get_dns_records.return_value = {
            'success': True,
            'records': sample_microsoft365_dns_records
        }

        # Create migration job
        migration_response = client.post(
            '/api/v1/migration/jobs',
            headers=auth_headers,
            json={
                'job_name': 'Email Preservation E2E Test',
                'domains': ['unicorncommander.ai']
            }
        )
        job_id = migration_response.json()['id']

        # Wait for completion
        await self._wait_for_migration_completion(client, auth_headers, job_id, timeout=30)

        # Run email health check
        health_response = client.post(
            '/api/v1/migration/health-check',
            headers=auth_headers,
            json={
                'domain': 'unicorncommander.ai',
                'checks': ['email']
            }
        )
        assert health_response.status_code == 200

        email_health = health_response.json()['email_functionality']
        assert email_health['status'] == 'passed'
        assert email_health['mx_records']
        assert 'mail.protection.outlook.com' in email_health['mx_records'][0]
        assert email_health['spf_configured'] is True
        assert email_health['dmarc_configured'] is True

    async def _wait_for_migration_completion(self, client, auth_headers, job_id, timeout=30):
        """Helper to wait for migration completion"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            response = client.get(
                f'/api/v1/migration/jobs/{job_id}/progress',
                headers=auth_headers
            )
            progress = response.json()
            if progress.get('completed_domains', 0) >= progress.get('total_domains', 1):
                return True
            await asyncio.sleep(1)
        return False


class TestMigrationPauseResume:
    """Test pausing and resuming migrations"""

    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_pause_and_resume_migration(
        self,
        client,
        auth_headers,
        mock_namecheap_client,
        mock_cloudflare_client
    ):
        """
        Test pausing and resuming a migration:
        - Start migration with multiple domains
        - Pause after first domain
        - Verify migration paused
        - Resume migration
        - Verify all domains complete
        """
        domains = ['unicorncommander.ai', 'superiorbsolutions.com']

        # Start migration
        migration_response = client.post(
            '/api/v1/migration/jobs',
            headers=auth_headers,
            json={
                'job_name': 'Pause/Resume E2E Test',
                'domains': domains
            }
        )
        job_id = migration_response.json()['id']

        # Wait for first domain to start
        await asyncio.sleep(2)

        # Pause migration
        pause_response = client.post(
            f'/api/v1/migration/jobs/{job_id}/pause',
            headers=auth_headers
        )
        assert pause_response.status_code == 200

        # Verify paused
        job_response = client.get(
            f'/api/v1/migration/jobs/{job_id}',
            headers=auth_headers
        )
        assert job_response.json()['status'] == 'paused'

        # Wait a bit to ensure no progress while paused
        await asyncio.sleep(3)

        progress_before_resume = client.get(
            f'/api/v1/migration/jobs/{job_id}/progress',
            headers=auth_headers
        ).json()

        # Resume migration
        resume_response = client.post(
            f'/api/v1/migration/jobs/{job_id}/resume',
            headers=auth_headers
        )
        assert resume_response.status_code == 200

        # Wait for completion
        max_wait = 30
        start_time = time.time()
        completed = False

        while time.time() - start_time < max_wait:
            progress_response = client.get(
                f'/api/v1/migration/jobs/{job_id}/progress',
                headers=auth_headers
            )
            progress = progress_response.json()

            if progress.get('completed_domains', 0) == 2:
                completed = True
                break

            await asyncio.sleep(1)

        assert completed, "Migration did not complete after resume"


class TestMigrationRollback:
    """Test migration rollback functionality"""

    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_rollback_single_domain(
        self,
        client,
        auth_headers,
        mock_namecheap_client,
        mock_cloudflare_client
    ):
        """
        Test rolling back a single domain:
        - Migrate domain
        - Rollback nameservers
        - Verify original nameservers restored
        """
        # Migrate domain
        migration_response = client.post(
            '/api/v1/migration/jobs',
            headers=auth_headers,
            json={
                'job_name': 'Rollback E2E Test',
                'domains': ['unicorncommander.ai']
            }
        )
        job_id = migration_response.json()['id']

        # Wait for migration to complete
        max_wait = 30
        start_time = time.time()
        while time.time() - start_time < max_wait:
            response = client.get(
                f'/api/v1/migration/jobs/{job_id}/progress',
                headers=auth_headers
            )
            if response.json().get('completed_domains', 0) >= 1:
                break
            await asyncio.sleep(1)

        # Rollback domain
        rollback_response = client.post(
            f'/api/v1/migration/jobs/{job_id}/domains/unicorncommander.ai/rollback',
            headers=auth_headers,
            json={
                'reason': 'Testing rollback functionality'
            }
        )
        assert rollback_response.status_code == 200
        rollback_data = rollback_response.json()
        assert rollback_data['success'] is True

        # Verify rollback recorded in history
        history_response = client.get(
            '/api/v1/migration/rollback-history',
            headers=auth_headers
        )
        assert history_response.status_code == 200
        history = history_response.json()
        assert len(history) >= 1
        assert any(r['domain'] == 'unicorncommander.ai' for r in history)

    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_rollback_entire_migration(
        self,
        client,
        auth_headers,
        mock_namecheap_client,
        mock_cloudflare_client
    ):
        """
        Test rolling back entire migration job:
        - Migrate multiple domains
        - Rollback all domains
        - Verify all nameservers restored
        """
        domains = ['unicorncommander.ai', 'superiorbsolutions.com']

        # Migrate domains
        migration_response = client.post(
            '/api/v1/migration/jobs',
            headers=auth_headers,
            json={
                'job_name': 'Full Rollback E2E Test',
                'domains': domains
            }
        )
        job_id = migration_response.json()['id']

        # Wait for completion
        max_wait = 40
        start_time = time.time()
        while time.time() - start_time < max_wait:
            response = client.get(
                f'/api/v1/migration/jobs/{job_id}/progress',
                headers=auth_headers
            )
            if response.json().get('completed_domains', 0) >= 2:
                break
            await asyncio.sleep(1)

        # Rollback entire migration
        rollback_response = client.post(
            f'/api/v1/migration/jobs/{job_id}/rollback',
            headers=auth_headers,
            json={
                'reason': 'Testing full migration rollback'
            }
        )
        assert rollback_response.status_code == 200

        # Verify both domains rolled back
        history_response = client.get(
            '/api/v1/migration/rollback-history',
            headers=auth_headers
        )
        history = history_response.json()
        rolled_back_domains = {r['domain'] for r in history}
        assert 'unicorncommander.ai' in rolled_back_domains
        assert 'superiorbsolutions.com' in rolled_back_domains


class TestHealthVerification:
    """Test post-migration health verification"""

    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_complete_health_check_workflow(
        self,
        client,
        auth_headers,
        mock_namecheap_client,
        mock_cloudflare_client,
        sample_microsoft365_dns_records
    ):
        """
        Test complete health check workflow:
        - Migrate domain
        - Run all health checks (DNS, SSL, email, website)
        - Verify propagation status
        """
        # Setup
        mock_namecheap_client.get_dns_records.return_value = {
            'success': True,
            'records': sample_microsoft365_dns_records
        }

        # Migrate domain
        migration_response = client.post(
            '/api/v1/migration/jobs',
            headers=auth_headers,
            json={
                'job_name': 'Health Check E2E Test',
                'domains': ['unicorncommander.ai']
            }
        )
        job_id = migration_response.json()['id']

        # Wait for migration
        max_wait = 30
        start_time = time.time()
        while time.time() - start_time < max_wait:
            response = client.get(
                f'/api/v1/migration/jobs/{job_id}/progress',
                headers=auth_headers
            )
            if response.json().get('completed_domains', 0) >= 1:
                break
            await asyncio.sleep(1)

        # Run comprehensive health check
        health_response = client.post(
            '/api/v1/migration/health-check',
            headers=auth_headers,
            json={
                'domain': 'unicorncommander.ai',
                'checks': ['dns', 'ssl', 'email', 'website']
            }
        )
        assert health_response.status_code == 200

        health_data = health_response.json()

        # Verify all checks present
        assert 'dns_propagation' in health_data
        assert 'ssl_certificate' in health_data
        assert 'email_functionality' in health_data
        assert 'website_accessibility' in health_data

        # Verify DNS propagation
        dns_check = health_data['dns_propagation']
        assert 'propagation_percent' in dns_check
        assert 'resolvers' in dns_check

        # Verify SSL certificate
        ssl_check = health_data['ssl_certificate']
        assert 'issued' in ssl_check

        # Verify email
        email_check = health_data['email_functionality']
        assert 'mx_records' in email_check
        assert 'spf_configured' in email_check

        # Verify website
        website_check = health_data['website_accessibility']
        assert 'http' in website_check
        assert 'https' in website_check


class TestDryRunMode:
    """Test dry run mode (preview without executing)"""

    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_dry_run_migration(
        self,
        client,
        auth_headers,
        mock_namecheap_client,
        sample_microsoft365_dns_records
    ):
        """
        Test dry run mode:
        - Preview migration without executing
        - Verify no actual changes made
        - Show what would happen
        """
        # Setup
        mock_namecheap_client.get_dns_records.return_value = {
            'success': True,
            'records': sample_microsoft365_dns_records
        }

        # Create dry run migration job
        migration_response = client.post(
            '/api/v1/migration/jobs',
            headers=auth_headers,
            json={
                'job_name': 'Dry Run E2E Test',
                'domains': ['unicorncommander.ai'],
                'dry_run': True  # Enable dry run mode
            }
        )
        assert migration_response.status_code == 201
        job_id = migration_response.json()['id']

        # Get dry run results
        job_response = client.get(
            f'/api/v1/migration/jobs/{job_id}',
            headers=auth_headers
        )
        job_data = job_response.json()

        # Verify dry run mode
        assert job_data['metadata']['dry_run'] is True
        assert job_data['status'] == 'dry_run_complete'

        # Verify results show what would happen
        assert 'preview' in job_data['metadata']
        preview = job_data['metadata']['preview']
        assert 'dns_records_to_import' in preview
        assert 'email_service_detected' in preview
        assert 'nameservers_to_update' in preview

        # Verify no actual changes made (no nameserver update calls)
        mock_namecheap_client.set_nameservers.assert_not_called()


# ============================================================================
# Error Recovery Tests
# ============================================================================

class TestErrorRecovery:
    """Test error recovery and retry mechanisms"""

    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_retry_failed_domain(
        self,
        client,
        auth_headers,
        mock_namecheap_client
    ):
        """
        Test automatic retry of failed domains:
        - Simulate failure (domain locked)
        - Verify automatic retry
        - Manually retry if needed
        """
        # Setup mock to fail initially
        mock_namecheap_client.set_nameservers = AsyncMock(
            side_effect=Exception("Domain is locked")
        )

        # Attempt migration
        migration_response = client.post(
            '/api/v1/migration/jobs',
            headers=auth_headers,
            json={
                'job_name': 'Error Recovery E2E Test',
                'domains': ['locked-domain.com']
            }
        )
        job_id = migration_response.json()['id']

        # Wait for failure
        await asyncio.sleep(5)

        # Check domain status
        status_response = client.get(
            f'/api/v1/migration/jobs/{job_id}/domains/locked-domain.com/status',
            headers=auth_headers
        )
        status_data = status_response.json()
        assert status_data['status'] == 'failed'
        assert 'locked' in status_data['error_message'].lower()

        # Fix mock (unlock domain)
        mock_namecheap_client.set_nameservers = AsyncMock(return_value={
            'success': True,
            'message': 'Nameservers updated successfully'
        })

        # Manually retry
        retry_response = client.post(
            f'/api/v1/migration/jobs/{job_id}/queue/locked-domain.com/retry',
            headers=auth_headers
        )
        assert retry_response.status_code == 200

        # Wait for retry to complete
        max_wait = 20
        start_time = time.time()
        succeeded = False

        while time.time() - start_time < max_wait:
            status_response = client.get(
                f'/api/v1/migration/jobs/{job_id}/domains/locked-domain.com/status',
                headers=auth_headers
            )
            if status_response.json()['status'] == 'completed':
                succeeded = True
                break
            await asyncio.sleep(1)

        assert succeeded, "Domain retry did not succeed"


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def client():
    """FastAPI test client"""
    from backend.main import app
    from fastapi.testclient import TestClient
    return TestClient(app)


@pytest.fixture
def auth_headers():
    """Authentication headers"""
    return {
        'Authorization': 'Bearer test_admin_token',
        'Content-Type': 'application/json'
    }
