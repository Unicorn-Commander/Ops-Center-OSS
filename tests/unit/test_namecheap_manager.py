"""
Unit Tests for NameCheap Manager (Epic 1.7)

Tests the NameCheapManager class methods including:
- Domain listing and filtering
- DNS export and parsing
- Email service detection (Microsoft 365, Private Email, Google)
- Nameserver updates
- Rollback capability
- Error handling

Target: 90%+ coverage
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import xml.etree.ElementTree as ET


# ============================================================================
# NameCheapManager Class Tests
# ============================================================================

class TestNameCheapManagerInitialization:
    """Test NameCheapManager initialization and configuration"""

    def test_init_with_valid_credentials(self):
        """Test initialization with valid credentials"""
        from backend.namecheap_manager import NameCheapManager

        manager = NameCheapManager(
            api_username='your-namecheap-username',
            api_key='test_api_key_123',
            client_ip='your-server-ip',
            sandbox_mode=False
        )

        assert manager.api_username == 'your-namecheap-username'
        assert manager.api_key == 'test_api_key_123'
        assert manager.client_ip == 'your-server-ip'
        assert manager.sandbox_mode is False

    def test_init_with_sandbox_mode(self):
        """Test initialization with sandbox mode enabled"""
        from backend.namecheap_manager import NameCheapManager

        manager = NameCheapManager(
            api_username='test',
            api_key='test_key',
            client_ip='127.0.0.1',
            sandbox_mode=True
        )

        assert manager.sandbox_mode is True
        assert 'sandbox' in manager.api_endpoint

    def test_init_missing_credentials(self):
        """Test initialization fails with missing credentials"""
        from backend.namecheap_manager import NameCheapManager

        with pytest.raises(ValueError, match="API username is required"):
            NameCheapManager(
                api_username='',
                api_key='test_key',
                client_ip='127.0.0.1'
            )


class TestDomainListing:
    """Test domain listing and filtering"""

    @pytest.mark.asyncio
    async def test_get_domain_list_success(self, mock_namecheap_client):
        """Test successful domain list retrieval"""
        from backend.namecheap_manager import NameCheapManager

        manager = NameCheapManager(
            api_username='test',
            api_key='test_key',
            client_ip='127.0.0.1'
        )
        manager.client = mock_namecheap_client

        result = await manager.get_domain_list()

        assert result['success'] is True
        assert len(result['domains']) == 4
        assert result['domains'][0]['name'] == 'unicorncommander.ai'

    @pytest.mark.asyncio
    async def test_filter_domains_by_status(self, mock_namecheap_client):
        """Test filtering domains by status"""
        from backend.namecheap_manager import NameCheapManager

        manager = NameCheapManager(
            api_username='test',
            api_key='test_key',
            client_ip='127.0.0.1'
        )
        manager.client = mock_namecheap_client

        # Get all domains
        all_domains = await manager.get_domain_list()

        # Filter active domains
        active_domains = [d for d in all_domains['domains'] if d['status'] == 'active']
        assert len(active_domains) == 3

        # Filter expired domains
        expired_domains = [d for d in all_domains['domains'] if d['status'] == 'expired']
        assert len(expired_domains) == 1
        assert expired_domains[0]['name'] == 'expired-domain.com'

    @pytest.mark.asyncio
    async def test_filter_domains_by_tld(self, mock_namecheap_client):
        """Test filtering domains by TLD"""
        from backend.namecheap_manager import NameCheapManager

        manager = NameCheapManager(
            api_username='test',
            api_key='test_key',
            client_ip='127.0.0.1'
        )
        manager.client = mock_namecheap_client

        all_domains = await manager.get_domain_list()

        # Filter .com domains
        com_domains = [d for d in all_domains['domains'] if d['tld'] == 'com']
        assert len(com_domains) == 3

        # Filter .ai domains
        ai_domains = [d for d in all_domains['domains'] if d['tld'] == 'ai']
        assert len(ai_domains) == 1
        assert ai_domains[0]['name'] == 'unicorncommander.ai'

    @pytest.mark.asyncio
    async def test_filter_locked_domains(self, mock_namecheap_client):
        """Test filtering locked domains"""
        from backend.namecheap_manager import NameCheapManager

        manager = NameCheapManager(
            api_username='test',
            api_key='test_key',
            client_ip='127.0.0.1'
        )
        manager.client = mock_namecheap_client

        all_domains = await manager.get_domain_list()

        # Filter locked domains
        locked_domains = [d for d in all_domains['domains'] if d['is_locked']]
        assert len(locked_domains) == 1
        assert locked_domains[0]['name'] == 'locked-domain.com'


class TestDNSExport:
    """Test DNS export and parsing"""

    @pytest.mark.asyncio
    async def test_export_dns_records_json(self, mock_namecheap_client, sample_basic_dns_records):
        """Test exporting DNS records in JSON format"""
        from backend.namecheap_manager import NameCheapManager

        manager = NameCheapManager(
            api_username='test',
            api_key='test_key',
            client_ip='127.0.0.1'
        )
        manager.client = mock_namecheap_client
        mock_namecheap_client.get_dns_records.return_value = {
            'success': True,
            'records': sample_basic_dns_records
        }

        result = await manager.export_dns_records('unicorncommander.ai', format='json')

        assert result['success'] is True
        assert result['format'] == 'json'
        assert len(result['records']) == 3
        assert result['domain'] == 'unicorncommander.ai'

    @pytest.mark.asyncio
    async def test_export_dns_records_csv(self, mock_namecheap_client, sample_basic_dns_records):
        """Test exporting DNS records in CSV format"""
        from backend.namecheap_manager import NameCheapManager

        manager = NameCheapManager(
            api_username='test',
            api_key='test_key',
            client_ip='127.0.0.1'
        )
        manager.client = mock_namecheap_client
        mock_namecheap_client.get_dns_records.return_value = {
            'success': True,
            'records': sample_basic_dns_records
        }

        result = await manager.export_dns_records('unicorncommander.ai', format='csv')

        assert result['success'] is True
        assert result['format'] == 'csv'
        assert 'type,host,value,ttl' in result['csv_data']

    @pytest.mark.asyncio
    async def test_export_dns_records_bind(self, mock_namecheap_client, sample_basic_dns_records):
        """Test exporting DNS records in BIND format"""
        from backend.namecheap_manager import NameCheapManager

        manager = NameCheapManager(
            api_username='test',
            api_key='test_key',
            client_ip='127.0.0.1'
        )
        manager.client = mock_namecheap_client
        mock_namecheap_client.get_dns_records.return_value = {
            'success': True,
            'records': sample_basic_dns_records
        }

        result = await manager.export_dns_records('unicorncommander.ai', format='bind')

        assert result['success'] is True
        assert result['format'] == 'bind'
        assert '@' in result['bind_zone']
        assert 'IN A' in result['bind_zone']

    @pytest.mark.asyncio
    async def test_parse_all_record_types(self, mock_namecheap_client, sample_all_record_types):
        """Test parsing all supported DNS record types"""
        from backend.namecheap_manager import NameCheapManager

        manager = NameCheapManager(
            api_username='test',
            api_key='test_key',
            client_ip='127.0.0.1'
        )
        manager.client = mock_namecheap_client
        mock_namecheap_client.get_dns_records.return_value = {
            'success': True,
            'records': sample_all_record_types
        }

        result = await manager.get_dns_records('example.com')

        assert result['success'] is True
        record_types = {r['type'] for r in result['records']}
        assert 'A' in record_types
        assert 'AAAA' in record_types
        assert 'CNAME' in record_types
        assert 'MX' in record_types
        assert 'TXT' in record_types
        assert 'SRV' in record_types
        assert 'CAA' in record_types
        assert 'NS' in record_types


class TestEmailServiceDetection:
    """Test email service detection"""

    @pytest.mark.asyncio
    async def test_detect_microsoft365(self, mock_namecheap_client, sample_microsoft365_dns_records):
        """Test detecting Microsoft 365 email service"""
        from backend.namecheap_manager import NameCheapManager

        manager = NameCheapManager(
            api_username='test',
            api_key='test_key',
            client_ip='127.0.0.1'
        )
        manager.client = mock_namecheap_client
        mock_namecheap_client.get_dns_records.return_value = {
            'success': True,
            'records': sample_microsoft365_dns_records
        }

        result = await manager.detect_email_service('unicorncommander.ai')

        assert result['service_type'] == 'microsoft365'
        assert 'mail.protection.outlook.com' in result['mx_records'][0]
        assert result['spf_configured'] is True
        assert result['dmarc_configured'] is True
        assert len(result['additional_records']) >= 2

    @pytest.mark.asyncio
    async def test_detect_namecheap_private_email(self, mock_namecheap_client, sample_namecheap_private_email_records):
        """Test detecting NameCheap Private Email service"""
        from backend.namecheap_manager import NameCheapManager

        manager = NameCheapManager(
            api_username='test',
            api_key='test_key',
            client_ip='127.0.0.1'
        )
        manager.client = mock_namecheap_client
        mock_namecheap_client.get_dns_records.return_value = {
            'success': True,
            'records': sample_namecheap_private_email_records
        }

        result = await manager.detect_email_service('magicunicorn.tech')

        assert result['service_type'] == 'namecheap_private'
        assert 'privateemail.com' in result['mx_records'][0]
        assert result['spf_configured'] is True
        assert len(result['mx_records']) == 2

    @pytest.mark.asyncio
    async def test_detect_google_workspace(self, mock_namecheap_client, sample_google_workspace_records):
        """Test detecting Google Workspace email service"""
        from backend.namecheap_manager import NameCheapManager

        manager = NameCheapManager(
            api_username='test',
            api_key='test_key',
            client_ip='127.0.0.1'
        )
        manager.client = mock_namecheap_client
        mock_namecheap_client.get_dns_records.return_value = {
            'success': True,
            'records': sample_google_workspace_records
        }

        result = await manager.detect_email_service('example.com')

        assert result['service_type'] == 'google_workspace'
        assert 'aspmx.l.google.com' in result['mx_records'][0]
        assert result['spf_configured'] is True
        assert len(result['mx_records']) >= 3

    @pytest.mark.asyncio
    async def test_no_email_service_detected(self, mock_namecheap_client, sample_basic_dns_records):
        """Test when no recognized email service is detected"""
        from backend.namecheap_manager import NameCheapManager

        manager = NameCheapManager(
            api_username='test',
            api_key='test_key',
            client_ip='127.0.0.1'
        )
        manager.client = mock_namecheap_client
        mock_namecheap_client.get_dns_records.return_value = {
            'success': True,
            'records': sample_basic_dns_records
        }

        result = await manager.detect_email_service('example.com')

        assert result['service_type'] == 'custom'
        assert len(result['mx_records']) >= 1


class TestNameserverUpdates:
    """Test nameserver update functionality"""

    @pytest.mark.asyncio
    async def test_update_nameservers_success(self, mock_namecheap_client):
        """Test successful nameserver update"""
        from backend.namecheap_manager import NameCheapManager

        manager = NameCheapManager(
            api_username='test',
            api_key='test_key',
            client_ip='127.0.0.1'
        )
        manager.client = mock_namecheap_client

        new_nameservers = ['vera.ns.cloudflare.com', 'walt.ns.cloudflare.com']
        result = await manager.update_nameservers('unicorncommander.ai', new_nameservers)

        assert result['success'] is True
        mock_namecheap_client.set_nameservers.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_nameservers_validates_format(self):
        """Test nameserver update validates nameserver format"""
        from backend.namecheap_manager import NameCheapManager

        manager = NameCheapManager(
            api_username='test',
            api_key='test_key',
            client_ip='127.0.0.1'
        )

        # Invalid nameservers (not enough)
        with pytest.raises(ValueError, match="At least 2 nameservers required"):
            await manager.update_nameservers('example.com', ['ns1.example.com'])

        # Invalid nameserver format
        with pytest.raises(ValueError, match="Invalid nameserver format"):
            await manager.update_nameservers('example.com', ['invalid ns', 'another invalid'])

    @pytest.mark.asyncio
    async def test_update_nameservers_domain_locked(self, mock_namecheap_error_client):
        """Test nameserver update fails for locked domain"""
        from backend.namecheap_manager import NameCheapManager

        manager = NameCheapManager(
            api_username='test',
            api_key='test_key',
            client_ip='127.0.0.1'
        )
        manager.client = mock_namecheap_error_client

        with pytest.raises(Exception, match="Domain is locked"):
            await manager.update_nameservers(
                'locked-domain.com',
                ['vera.ns.cloudflare.com', 'walt.ns.cloudflare.com']
            )

    @pytest.mark.asyncio
    async def test_batch_nameserver_updates(self, mock_namecheap_client):
        """Test batch nameserver updates for multiple domains"""
        from backend.namecheap_manager import NameCheapManager

        manager = NameCheapManager(
            api_username='test',
            api_key='test_key',
            client_ip='127.0.0.1'
        )
        manager.client = mock_namecheap_client

        domains = ['unicorncommander.ai', 'superiorbsolutions.com', 'magicunicorn.tech']
        new_nameservers = ['vera.ns.cloudflare.com', 'walt.ns.cloudflare.com']

        results = await manager.batch_update_nameservers(domains, new_nameservers)

        assert len(results) == 3
        assert all(r['success'] for r in results)
        assert mock_namecheap_client.set_nameservers.call_count == 3


class TestRollbackCapability:
    """Test rollback capability"""

    @pytest.mark.asyncio
    async def test_rollback_nameservers(self, mock_namecheap_client, sample_dns_backup):
        """Test rolling back nameservers to original values"""
        from backend.namecheap_manager import NameCheapManager

        manager = NameCheapManager(
            api_username='test',
            api_key='test_key',
            client_ip='127.0.0.1'
        )
        manager.client = mock_namecheap_client

        original_ns = sample_dns_backup['original_nameservers']
        result = await manager.rollback_nameservers('unicorncommander.ai', original_ns)

        assert result['success'] is True
        mock_namecheap_client.set_nameservers.assert_called_once_with(
            'unicorncommander.ai',
            original_ns
        )

    @pytest.mark.asyncio
    async def test_rollback_verifies_original_nameservers(self):
        """Test rollback verifies original nameservers exist"""
        from backend.namecheap_manager import NameCheapManager

        manager = NameCheapManager(
            api_username='test',
            api_key='test_key',
            client_ip='127.0.0.1'
        )

        # Rollback with no original nameservers should fail
        with pytest.raises(ValueError, match="Original nameservers not provided"):
            await manager.rollback_nameservers('example.com', [])

    @pytest.mark.asyncio
    async def test_rollback_tracks_history(self, mock_namecheap_client, mock_migration_db):
        """Test rollback is tracked in history"""
        from backend.namecheap_manager import NameCheapManager

        manager = NameCheapManager(
            api_username='test',
            api_key='test_key',
            client_ip='127.0.0.1'
        )
        manager.client = mock_namecheap_client
        manager.db = mock_migration_db

        original_ns = ['dns1.registrar-servers.com', 'dns2.registrar-servers.com']
        await manager.rollback_nameservers(
            'unicorncommander.ai',
            original_ns,
            reason='Email not working'
        )

        # Verify rollback was logged
        mock_migration_db.insert.assert_called_once()


class TestErrorHandling:
    """Test error handling"""

    @pytest.mark.asyncio
    async def test_api_rate_limit_error(self, mock_namecheap_error_client):
        """Test handling API rate limit errors"""
        from backend.namecheap_manager import NameCheapManager

        manager = NameCheapManager(
            api_username='test',
            api_key='test_key',
            client_ip='127.0.0.1'
        )
        manager.client = mock_namecheap_error_client

        with pytest.raises(Exception, match="API rate limit exceeded"):
            await manager.get_domain_list()

    @pytest.mark.asyncio
    async def test_xml_parsing_error(self):
        """Test handling XML parsing errors"""
        from backend.namecheap_manager import NameCheapManager

        manager = NameCheapManager(
            api_username='test',
            api_key='test_key',
            client_ip='127.0.0.1'
        )

        invalid_xml = "not valid xml"

        with pytest.raises(Exception, match="Failed to parse XML"):
            manager._parse_xml_response(invalid_xml)

    @pytest.mark.asyncio
    async def test_domain_not_found_error(self, mock_namecheap_error_client):
        """Test handling domain not found errors"""
        from backend.namecheap_manager import NameCheapManager

        manager = NameCheapManager(
            api_username='test',
            api_key='test_key',
            client_ip='127.0.0.1'
        )
        manager.client = mock_namecheap_error_client

        with pytest.raises(Exception, match="Domain not found"):
            await manager.get_dns_records('nonexistent-domain.com')

    @pytest.mark.asyncio
    async def test_connection_timeout(self):
        """Test handling connection timeouts"""
        from backend.namecheap_manager import NameCheapManager

        manager = NameCheapManager(
            api_username='test',
            api_key='test_key',
            client_ip='127.0.0.1',
            timeout=1  # 1 second timeout
        )

        # Mock a slow response
        manager.client = Mock()
        manager.client.get_domain_list = AsyncMock(
            side_effect=asyncio.TimeoutError("Connection timeout")
        )

        with pytest.raises(asyncio.TimeoutError):
            await manager.get_domain_list()


class TestIPWhitelisting:
    """Test IP whitelist verification"""

    @pytest.mark.asyncio
    async def test_verify_ip_whitelisted(self, mock_namecheap_client):
        """Test verifying IP is whitelisted"""
        from backend.namecheap_manager import NameCheapManager

        manager = NameCheapManager(
            api_username='test',
            api_key='test_key',
            client_ip='your-server-ip'
        )
        manager.client = mock_namecheap_client

        result = await manager.test_connection()

        assert result['success'] is True
        assert result['ip_whitelisted'] is True

    @pytest.mark.asyncio
    async def test_ip_not_whitelisted_error(self):
        """Test handling IP not whitelisted error"""
        from backend.namecheap_manager import NameCheapManager

        manager = NameCheapManager(
            api_username='test',
            api_key='test_key',
            client_ip='1.2.3.4'  # Not whitelisted
        )

        client = Mock()
        client.test_connection = AsyncMock(return_value={
            'success': False,
            'error': 'IP not whitelisted',
            'ip_whitelisted': False
        })
        manager.client = client

        result = await manager.test_connection()

        assert result['success'] is False
        assert result['ip_whitelisted'] is False


# ============================================================================
# Integration with Migration System Tests
# ============================================================================

class TestMigrationIntegration:
    """Test integration with migration system"""

    @pytest.mark.asyncio
    async def test_prepare_domain_for_migration(self, mock_namecheap_client, sample_microsoft365_dns_records):
        """Test preparing a domain for migration"""
        from backend.namecheap_manager import NameCheapManager

        manager = NameCheapManager(
            api_username='test',
            api_key='test_key',
            client_ip='127.0.0.1'
        )
        manager.client = mock_namecheap_client
        mock_namecheap_client.get_dns_records.return_value = {
            'success': True,
            'records': sample_microsoft365_dns_records
        }

        # Prepare domain for migration (export DNS, detect email)
        prep_result = await manager.prepare_for_migration('unicorncommander.ai')

        assert prep_result['success'] is True
        assert 'dns_backup' in prep_result
        assert 'email_service' in prep_result
        assert prep_result['email_service']['service_type'] == 'microsoft365'

    @pytest.mark.asyncio
    async def test_validate_migration_readiness(self, sample_active_domain):
        """Test validating domain is ready for migration"""
        from backend.namecheap_manager import NameCheapManager

        manager = NameCheapManager(
            api_username='test',
            api_key='test_key',
            client_ip='127.0.0.1'
        )

        # Active, unlocked domain should be ready
        result = manager.validate_migration_readiness(sample_active_domain)

        assert result['ready'] is True
        assert len(result['warnings']) == 0
        assert len(result['blockers']) == 0

    @pytest.mark.asyncio
    async def test_validate_locked_domain_not_ready(self, sample_locked_domain):
        """Test locked domain is not ready for migration"""
        from backend.namecheap_manager import NameCheapManager

        manager = NameCheapManager(
            api_username='test',
            api_key='test_key',
            client_ip='127.0.0.1'
        )

        # Locked domain should not be ready
        result = manager.validate_migration_readiness(sample_locked_domain)

        assert result['ready'] is False
        assert 'locked' in result['blockers'][0].lower()

    @pytest.mark.asyncio
    async def test_validate_expired_domain_not_ready(self, sample_expired_domain):
        """Test expired domain is not ready for migration"""
        from backend.namecheap_manager import NameCheapManager

        manager = NameCheapManager(
            api_username='test',
            api_key='test_key',
            client_ip='127.0.0.1'
        )

        # Expired domain should not be ready
        result = manager.validate_migration_readiness(sample_expired_domain)

        assert result['ready'] is False
        assert 'expired' in result['blockers'][0].lower()
