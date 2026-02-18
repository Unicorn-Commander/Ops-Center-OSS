"""
Integration Tests for Migration API Endpoints (Epic 1.7)

Tests all 20 migration API endpoints including:
- 5-phase workflow (Discovery → Export → Review → Execute → Verify)
- Authentication and authorization
- Rate limiting (10 req/min)
- Migration job tracking
- Rollback execution
- Health checks (DNS, SSL, email, website)

Mocks both NameCheap and Cloudflare APIs
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock, patch
import json


# ============================================================================
# API Endpoint Tests - NameCheap Integration
# ============================================================================

class TestNameCheapAccountManagement:
    """Test NameCheap account management endpoints"""

    def test_create_namecheap_account(self, client: TestClient, auth_headers):
        """Test POST /api/v1/namecheap/accounts - Create account"""
        response = client.post(
            '/api/v1/namecheap/accounts',
            headers=auth_headers,
            json={
                'account_label': 'My Business Account',
                'api_username': 'your-namecheap-username',
                'api_key': 'test_api_key_123',
                'client_ip': 'your-server-ip',
                'sandbox_mode': False
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data['account_label'] == 'My Business Account'
        assert data['api_username'] == 'your-namecheap-username'
        assert 'id' in data

    def test_get_namecheap_accounts(self, client: TestClient, auth_headers):
        """Test GET /api/v1/namecheap/accounts - List accounts"""
        response = client.get('/api/v1/namecheap/accounts', headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_test_namecheap_connection(self, client: TestClient, auth_headers, mock_namecheap_client):
        """Test POST /api/v1/namecheap/accounts/{id}/test-connection"""
        # First create account
        create_response = client.post(
            '/api/v1/namecheap/accounts',
            headers=auth_headers,
            json={
                'account_label': 'Test Account',
                'api_username': 'test',
                'api_key': 'test_key',
                'client_ip': '127.0.0.1'
            }
        )
        account_id = create_response.json()['id']

        # Test connection
        with patch('backend.namecheap_manager.NameCheapManager') as mock_manager:
            mock_manager.return_value.test_connection = mock_namecheap_client.test_connection

            response = client.post(
                f'/api/v1/namecheap/accounts/{account_id}/test-connection',
                headers=auth_headers
            )

            assert response.status_code == 200
            data = response.json()
            assert data['success'] is True
            assert data['ip_whitelisted'] is True

    def test_delete_namecheap_account(self, client: TestClient, auth_headers):
        """Test DELETE /api/v1/namecheap/accounts/{id}"""
        # Create account
        create_response = client.post(
            '/api/v1/namecheap/accounts',
            headers=auth_headers,
            json={
                'account_label': 'To Delete',
                'api_username': 'test',
                'api_key': 'test_key',
                'client_ip': '127.0.0.1'
            }
        )
        account_id = create_response.json()['id']

        # Delete account
        response = client.delete(
            f'/api/v1/namecheap/accounts/{account_id}',
            headers=auth_headers
        )

        assert response.status_code == 200
        assert response.json()['success'] is True


class TestDomainDiscovery:
    """Test domain discovery endpoints"""

    def test_sync_domains_from_namecheap(self, client: TestClient, auth_headers, mock_namecheap_client):
        """Test POST /api/v1/namecheap/domains/sync"""
        with patch('backend.namecheap_manager.NameCheapManager') as mock_manager:
            mock_manager.return_value.get_domain_list = mock_namecheap_client.get_domain_list

            response = client.post(
                '/api/v1/namecheap/domains/sync',
                headers=auth_headers,
                params={'account_id': 'test_account_id'}
            )

            assert response.status_code == 200
            data = response.json()
            assert data['success'] is True
            assert 'domains_synced' in data
            assert data['domains_synced'] == 4

    def test_get_domains_with_filter(self, client: TestClient, auth_headers):
        """Test GET /api/v1/namecheap/domains with filters"""
        response = client.get(
            '/api/v1/namecheap/domains',
            headers=auth_headers,
            params={
                'account_id': 'test_account_id',
                'status': 'active',
                'tld': 'com'
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestDNSExport:
    """Test DNS export endpoints"""

    def test_get_dns_records(self, client: TestClient, auth_headers, mock_namecheap_client, sample_basic_dns_records):
        """Test GET /api/v1/namecheap/domains/{domain}/dns"""
        with patch('backend.namecheap_manager.NameCheapManager') as mock_manager:
            mock_manager.return_value.get_dns_records = AsyncMock(return_value={
                'success': True,
                'records': sample_basic_dns_records
            })

            response = client.get(
                '/api/v1/namecheap/domains/unicorncommander.ai/dns',
                headers=auth_headers
            )

            assert response.status_code == 200
            data = response.json()
            assert len(data['records']) == 3

    def test_export_dns_json(self, client: TestClient, auth_headers, mock_namecheap_client):
        """Test POST /api/v1/namecheap/domains/{domain}/dns/export - JSON format"""
        response = client.post(
            '/api/v1/namecheap/domains/unicorncommander.ai/dns/export',
            headers=auth_headers,
            params={'format': 'json'}
        )

        assert response.status_code == 200
        data = response.json()
        assert data['format'] == 'json'
        assert 'records' in data

    def test_export_dns_csv(self, client: TestClient, auth_headers):
        """Test POST /api/v1/namecheap/domains/{domain}/dns/export - CSV format"""
        response = client.post(
            '/api/v1/namecheap/domains/unicorncommander.ai/dns/export',
            headers=auth_headers,
            params={'format': 'csv'}
        )

        assert response.status_code == 200
        assert response.headers['content-type'] == 'text/csv'

    def test_export_dns_bind(self, client: TestClient, auth_headers):
        """Test POST /api/v1/namecheap/domains/{domain}/dns/export - BIND format"""
        response = client.post(
            '/api/v1/namecheap/domains/unicorncommander.ai/dns/export',
            headers=auth_headers,
            params={'format': 'bind'}
        )

        assert response.status_code == 200
        assert response.headers['content-type'] == 'text/plain'


# ============================================================================
# API Endpoint Tests - Migration Workflow
# ============================================================================

class TestMigrationJobManagement:
    """Test migration job endpoints"""

    def test_create_migration_job(self, client: TestClient, auth_headers):
        """Test POST /api/v1/migration/jobs - Start migration"""
        response = client.post(
            '/api/v1/migration/jobs',
            headers=auth_headers,
            json={
                'job_name': 'Test Migration',
                'domains': ['unicorncommander.ai', 'superiorbsolutions.com'],
                'priority': 'high'
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data['job_name'] == 'Test Migration'
        assert data['total_domains'] == 2
        assert data['status'] == 'pending'
        assert 'id' in data

    def test_get_migration_jobs(self, client: TestClient, auth_headers):
        """Test GET /api/v1/migration/jobs - List migrations"""
        response = client.get('/api/v1/migration/jobs', headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_migration_job_details(self, client: TestClient, auth_headers):
        """Test GET /api/v1/migration/jobs/{job_id}"""
        # Create job first
        create_response = client.post(
            '/api/v1/migration/jobs',
            headers=auth_headers,
            json={
                'job_name': 'Test Migration',
                'domains': ['unicorncommander.ai']
            }
        )
        job_id = create_response.json()['id']

        # Get job details
        response = client.get(
            f'/api/v1/migration/jobs/{job_id}',
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data['id'] == job_id
        assert 'status' in data

    def test_cancel_migration_job(self, client: TestClient, auth_headers):
        """Test DELETE /api/v1/migration/jobs/{job_id} - Cancel migration"""
        # Create job
        create_response = client.post(
            '/api/v1/migration/jobs',
            headers=auth_headers,
            json={
                'job_name': 'To Cancel',
                'domains': ['unicorncommander.ai']
            }
        )
        job_id = create_response.json()['id']

        # Cancel job
        response = client.delete(
            f'/api/v1/migration/jobs/{job_id}',
            headers=auth_headers
        )

        assert response.status_code == 200
        assert response.json()['status'] == 'cancelled'

    def test_pause_migration_job(self, client: TestClient, auth_headers):
        """Test POST /api/v1/migration/jobs/{job_id}/pause"""
        # Create job
        create_response = client.post(
            '/api/v1/migration/jobs',
            headers=auth_headers,
            json={
                'job_name': 'To Pause',
                'domains': ['unicorncommander.ai']
            }
        )
        job_id = create_response.json()['id']

        # Pause job
        response = client.post(
            f'/api/v1/migration/jobs/{job_id}/pause',
            headers=auth_headers
        )

        assert response.status_code == 200
        assert response.json()['status'] == 'paused'

    def test_resume_migration_job(self, client: TestClient, auth_headers):
        """Test POST /api/v1/migration/jobs/{job_id}/resume"""
        # Create and pause job
        create_response = client.post(
            '/api/v1/migration/jobs',
            headers=auth_headers,
            json={
                'job_name': 'To Resume',
                'domains': ['unicorncommander.ai']
            }
        )
        job_id = create_response.json()['id']

        client.post(f'/api/v1/migration/jobs/{job_id}/pause', headers=auth_headers)

        # Resume job
        response = client.post(
            f'/api/v1/migration/jobs/{job_id}/resume',
            headers=auth_headers
        )

        assert response.status_code == 200
        assert response.json()['status'] in ['pending', 'in_progress']


class TestMigrationQueue:
    """Test migration queue endpoints"""

    def test_get_migration_queue(self, client: TestClient, auth_headers):
        """Test GET /api/v1/migration/jobs/{job_id}/queue"""
        # Create job with multiple domains
        create_response = client.post(
            '/api/v1/migration/jobs',
            headers=auth_headers,
            json={
                'job_name': 'Queue Test',
                'domains': ['domain1.com', 'domain2.com', 'domain3.com']
            }
        )
        job_id = create_response.json()['id']

        # Get queue
        response = client.get(
            f'/api/v1/migration/jobs/{job_id}/queue',
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

    def test_retry_failed_domain(self, client: TestClient, auth_headers):
        """Test POST /api/v1/migration/jobs/{job_id}/queue/{domain}/retry"""
        # Create job
        create_response = client.post(
            '/api/v1/migration/jobs',
            headers=auth_headers,
            json={
                'job_name': 'Retry Test',
                'domains': ['unicorncommander.ai']
            }
        )
        job_id = create_response.json()['id']

        # Retry domain
        response = client.post(
            f'/api/v1/migration/jobs/{job_id}/queue/unicorncommander.ai/retry',
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data['domain'] == 'unicorncommander.ai'

    def test_update_domain_priority(self, client: TestClient, auth_headers):
        """Test PUT /api/v1/migration/jobs/{job_id}/queue/{domain}/priority"""
        # Create job
        create_response = client.post(
            '/api/v1/migration/jobs',
            headers=auth_headers,
            json={
                'job_name': 'Priority Test',
                'domains': ['unicorncommander.ai']
            }
        )
        job_id = create_response.json()['id']

        # Update priority
        response = client.put(
            f'/api/v1/migration/jobs/{job_id}/queue/unicorncommander.ai/priority',
            headers=auth_headers,
            json={'priority': 'critical'}
        )

        assert response.status_code == 200
        data = response.json()
        assert data['priority'] == 'critical'


class TestProgressTracking:
    """Test progress tracking endpoints"""

    def test_get_migration_progress(self, client: TestClient, auth_headers):
        """Test GET /api/v1/migration/jobs/{job_id}/progress"""
        # Create job
        create_response = client.post(
            '/api/v1/migration/jobs',
            headers=auth_headers,
            json={
                'job_name': 'Progress Test',
                'domains': ['unicorncommander.ai']
            }
        )
        job_id = create_response.json()['id']

        # Get progress
        response = client.get(
            f'/api/v1/migration/jobs/{job_id}/progress',
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert 'total_domains' in data
        assert 'completed_domains' in data
        assert 'progress_percent' in data

    def test_get_domain_status(self, client: TestClient, auth_headers):
        """Test GET /api/v1/migration/jobs/{job_id}/domains/{domain}/status"""
        # Create job
        create_response = client.post(
            '/api/v1/migration/jobs',
            headers=auth_headers,
            json={
                'job_name': 'Status Test',
                'domains': ['unicorncommander.ai']
            }
        )
        job_id = create_response.json()['id']

        # Get domain status
        response = client.get(
            f'/api/v1/migration/jobs/{job_id}/domains/unicorncommander.ai/status',
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data['domain'] == 'unicorncommander.ai'
        assert 'phase' in data
        assert 'status' in data


# ============================================================================
# API Endpoint Tests - Health Checks
# ============================================================================

class TestHealthChecks:
    """Test health check endpoints"""

    def test_run_full_health_check(self, client: TestClient, auth_headers):
        """Test POST /api/v1/migration/health-check"""
        response = client.post(
            '/api/v1/migration/health-check',
            headers=auth_headers,
            json={
                'domain': 'unicorncommander.ai',
                'checks': ['dns', 'ssl', 'email', 'website']
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert 'dns_propagation' in data
        assert 'ssl_certificate' in data
        assert 'email_functionality' in data
        assert 'website_accessibility' in data

    def test_get_job_health_checks(self, client: TestClient, auth_headers):
        """Test GET /api/v1/migration/jobs/{job_id}/health-checks"""
        # Create job
        create_response = client.post(
            '/api/v1/migration/jobs',
            headers=auth_headers,
            json={
                'job_name': 'Health Check Test',
                'domains': ['unicorncommander.ai']
            }
        )
        job_id = create_response.json()['id']

        # Get health checks
        response = client.get(
            f'/api/v1/migration/jobs/{job_id}/health-checks',
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_run_domain_health_check(self, client: TestClient, auth_headers):
        """Test POST /api/v1/migration/jobs/{job_id}/domains/{domain}/health-check"""
        # Create job
        create_response = client.post(
            '/api/v1/migration/jobs',
            headers=auth_headers,
            json={
                'job_name': 'Domain Health Test',
                'domains': ['unicorncommander.ai']
            }
        )
        job_id = create_response.json()['id']

        # Run health check
        response = client.post(
            f'/api/v1/migration/jobs/{job_id}/domains/unicorncommander.ai/health-check',
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert 'status' in data


# ============================================================================
# API Endpoint Tests - Rollback
# ============================================================================

class TestRollback:
    """Test rollback endpoints"""

    def test_rollback_full_migration(self, client: TestClient, auth_headers):
        """Test POST /api/v1/migration/jobs/{job_id}/rollback"""
        # Create job
        create_response = client.post(
            '/api/v1/migration/jobs',
            headers=auth_headers,
            json={
                'job_name': 'Rollback Test',
                'domains': ['unicorncommander.ai']
            }
        )
        job_id = create_response.json()['id']

        # Rollback migration
        response = client.post(
            f'/api/v1/migration/jobs/{job_id}/rollback',
            headers=auth_headers,
            json={
                'reason': 'Testing rollback functionality'
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True

    def test_rollback_single_domain(self, client: TestClient, auth_headers):
        """Test POST /api/v1/migration/jobs/{job_id}/domains/{domain}/rollback"""
        # Create job
        create_response = client.post(
            '/api/v1/migration/jobs',
            headers=auth_headers,
            json={
                'job_name': 'Domain Rollback Test',
                'domains': ['unicorncommander.ai', 'superiorbsolutions.com']
            }
        )
        job_id = create_response.json()['id']

        # Rollback single domain
        response = client.post(
            f'/api/v1/migration/jobs/{job_id}/domains/unicorncommander.ai/rollback',
            headers=auth_headers,
            json={
                'reason': 'Email not working'
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data['domain'] == 'unicorncommander.ai'

    def test_get_rollback_history(self, client: TestClient, auth_headers):
        """Test GET /api/v1/migration/rollback-history"""
        response = client.get(
            '/api/v1/migration/rollback-history',
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


# ============================================================================
# Rate Limiting Tests
# ============================================================================

class TestRateLimiting:
    """Test API rate limiting (10 req/min)"""

    def test_rate_limit_enforcement(self, client: TestClient, auth_headers):
        """Test rate limiting is enforced at 10 requests per minute"""
        # Make 11 requests rapidly
        responses = []
        for i in range(11):
            response = client.get(
                '/api/v1/namecheap/domains',
                headers=auth_headers
            )
            responses.append(response)

        # First 10 should succeed
        assert all(r.status_code == 200 for r in responses[:10])

        # 11th should be rate limited
        assert responses[10].status_code == 429
        assert 'rate limit' in responses[10].json()['error'].lower()

    def test_rate_limit_per_user(self, client: TestClient):
        """Test rate limiting is per-user"""
        # Create two different auth headers
        auth_headers_1 = {'Authorization': 'Bearer user1_token'}
        auth_headers_2 = {'Authorization': 'Bearer user2_token'}

        # User 1 makes 10 requests
        for i in range(10):
            client.get('/api/v1/namecheap/domains', headers=auth_headers_1)

        # User 2 should still be able to make requests
        response = client.get(
            '/api/v1/namecheap/domains',
            headers=auth_headers_2
        )
        assert response.status_code == 200


# ============================================================================
# Authentication & Authorization Tests
# ============================================================================

class TestAuthentication:
    """Test authentication and authorization"""

    def test_unauthenticated_request_rejected(self, client: TestClient):
        """Test requests without authentication are rejected"""
        response = client.get('/api/v1/namecheap/accounts')

        assert response.status_code == 401
        assert 'authentication' in response.json()['error'].lower()

    def test_invalid_token_rejected(self, client: TestClient):
        """Test requests with invalid tokens are rejected"""
        response = client.get(
            '/api/v1/namecheap/accounts',
            headers={'Authorization': 'Bearer invalid_token'}
        )

        assert response.status_code == 401

    def test_admin_only_endpoints_require_admin(self, client: TestClient, user_auth_headers):
        """Test admin-only endpoints require admin role"""
        # Non-admin user tries to delete account
        response = client.delete(
            '/api/v1/namecheap/accounts/test_id',
            headers=user_auth_headers
        )

        assert response.status_code == 403
        assert 'admin' in response.json()['error'].lower()


# ============================================================================
# Error Handling Tests
# ============================================================================

class TestErrorHandling:
    """Test API error handling"""

    def test_invalid_domain_format(self, client: TestClient, auth_headers):
        """Test handling invalid domain format"""
        response = client.get(
            '/api/v1/namecheap/domains/invalid domain/dns',
            headers=auth_headers
        )

        assert response.status_code == 400
        assert 'invalid domain' in response.json()['error'].lower()

    def test_nonexistent_job_id(self, client: TestClient, auth_headers):
        """Test handling nonexistent job ID"""
        response = client.get(
            '/api/v1/migration/jobs/nonexistent-job-id',
            headers=auth_headers
        )

        assert response.status_code == 404
        assert 'not found' in response.json()['error'].lower()

    def test_missing_required_fields(self, client: TestClient, auth_headers):
        """Test handling missing required fields"""
        response = client.post(
            '/api/v1/migration/jobs',
            headers=auth_headers,
            json={
                'job_name': 'Test'
                # Missing 'domains' field
            }
        )

        assert response.status_code == 422
        assert 'domains' in response.json()['error'].lower()


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def client():
    """FastAPI test client"""
    from backend.main import app
    return TestClient(app)


@pytest.fixture
def auth_headers():
    """Authentication headers for admin user"""
    return {
        'Authorization': 'Bearer test_admin_token',
        'Content-Type': 'application/json'
    }


@pytest.fixture
def user_auth_headers():
    """Authentication headers for regular user"""
    return {
        'Authorization': 'Bearer test_user_token',
        'Content-Type': 'application/json'
    }
