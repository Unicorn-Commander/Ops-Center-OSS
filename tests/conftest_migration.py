"""
Pytest fixtures for Epic 1.7 NameCheap Migration Tests

Provides mock NameCheap API clients, sample domain data, DNS records,
email configurations, and migration job database mocks.
"""

import pytest
from datetime import datetime, timedelta
from typing import Dict, List, Any
from unittest.mock import Mock, AsyncMock, MagicMock
import json


# ============================================================================
# NameCheap API Mock Fixtures
# ============================================================================

@pytest.fixture
def mock_namecheap_client():
    """Mock NameCheap API client with standard responses"""
    client = Mock()

    # Mock successful API responses
    client.get_domain_list = AsyncMock(return_value={
        'success': True,
        'domains': [
            {
                'name': 'unicorncommander.ai',
                'tld': 'ai',
                'status': 'active',
                'is_locked': False,
                'is_premium': False,
                'expiration_date': (datetime.now() + timedelta(days=365)).isoformat(),
                'nameservers': ['dns1.registrar-servers.com', 'dns2.registrar-servers.com']
            },
            {
                'name': 'superiorbsolutions.com',
                'tld': 'com',
                'status': 'active',
                'is_locked': False,
                'is_premium': False,
                'expiration_date': (datetime.now() + timedelta(days=180)).isoformat(),
                'nameservers': ['dns1.registrar-servers.com', 'dns2.registrar-servers.com']
            },
            {
                'name': 'expired-domain.com',
                'tld': 'com',
                'status': 'expired',
                'is_locked': False,
                'is_premium': False,
                'expiration_date': (datetime.now() - timedelta(days=30)).isoformat(),
                'nameservers': ['dns1.registrar-servers.com', 'dns2.registrar-servers.com']
            },
            {
                'name': 'locked-domain.com',
                'tld': 'com',
                'status': 'active',
                'is_locked': True,
                'is_premium': False,
                'expiration_date': (datetime.now() + timedelta(days=200)).isoformat(),
                'nameservers': ['dns1.registrar-servers.com', 'dns2.registrar-servers.com']
            }
        ]
    })

    client.get_dns_records = AsyncMock(return_value={
        'success': True,
        'records': []  # Will be populated by specific tests
    })

    client.set_nameservers = AsyncMock(return_value={
        'success': True,
        'message': 'Nameservers updated successfully'
    })

    client.test_connection = AsyncMock(return_value={
        'success': True,
        'account_balance': '1234.56',
        'domain_count': 12,
        'ip_whitelisted': True
    })

    return client


@pytest.fixture
def mock_namecheap_error_client():
    """Mock NameCheap API client that returns errors"""
    client = Mock()

    client.get_domain_list = AsyncMock(side_effect=Exception("API rate limit exceeded"))
    client.get_dns_records = AsyncMock(side_effect=Exception("Domain not found"))
    client.set_nameservers = AsyncMock(side_effect=Exception("Domain is locked"))

    return client


# ============================================================================
# Sample Domain Data Fixtures
# ============================================================================

@pytest.fixture
def sample_active_domain():
    """Sample active domain data"""
    return {
        'id': '550e8400-e29b-41d4-a716-446655440000',
        'domain': 'unicorncommander.ai',
        'tld': 'ai',
        'status': 'active',
        'current_nameservers': ['dns1.registrar-servers.com', 'dns2.registrar-servers.com'],
        'expiration_date': (datetime.now() + timedelta(days=365)).isoformat(),
        'is_premium': False,
        'is_locked': False,
        'whois_guard': True,
        'last_synced': datetime.now().isoformat(),
        'metadata': {}
    }


@pytest.fixture
def sample_expired_domain():
    """Sample expired domain data"""
    return {
        'id': '550e8400-e29b-41d4-a716-446655440001',
        'domain': 'expired-domain.com',
        'tld': 'com',
        'status': 'expired',
        'current_nameservers': ['dns1.registrar-servers.com', 'dns2.registrar-servers.com'],
        'expiration_date': (datetime.now() - timedelta(days=30)).isoformat(),
        'is_premium': False,
        'is_locked': False,
        'whois_guard': True,
        'last_synced': datetime.now().isoformat(),
        'metadata': {}
    }


@pytest.fixture
def sample_locked_domain():
    """Sample locked domain data"""
    return {
        'id': '550e8400-e29b-41d4-a716-446655440002',
        'domain': 'locked-domain.com',
        'tld': 'com',
        'status': 'active',
        'current_nameservers': ['dns1.registrar-servers.com', 'dns2.registrar-servers.com'],
        'expiration_date': (datetime.now() + timedelta(days=200)).isoformat(),
        'is_premium': False,
        'is_locked': True,
        'whois_guard': True,
        'last_synced': datetime.now().isoformat(),
        'metadata': {}
    }


# ============================================================================
# DNS Records Fixtures
# ============================================================================

@pytest.fixture
def sample_basic_dns_records():
    """Sample basic DNS records (A, CNAME, MX)"""
    return [
        {
            'type': 'A',
            'host': '@',
            'value': 'your-server-ip',
            'ttl': 1800
        },
        {
            'type': 'CNAME',
            'host': 'www',
            'value': 'unicorncommander.ai',
            'ttl': 1800
        },
        {
            'type': 'MX',
            'host': '@',
            'value': 'mail.example.com',
            'priority': 10,
            'ttl': 3600
        }
    ]


@pytest.fixture
def sample_microsoft365_dns_records():
    """Sample Microsoft 365 email DNS records"""
    return [
        {
            'type': 'A',
            'host': '@',
            'value': 'your-server-ip',
            'ttl': 1800
        },
        {
            'type': 'MX',
            'host': '@',
            'value': 'superiorbsolutions-com.mail.protection.outlook.com',
            'priority': 0,
            'ttl': 3600
        },
        {
            'type': 'TXT',
            'host': '@',
            'value': 'v=spf1 include:spf.protection.outlook.com -all',
            'ttl': 3600
        },
        {
            'type': 'TXT',
            'host': '_dmarc',
            'value': 'v=DMARC1; p=none; rua=mailto:dmarc@example.com',
            'ttl': 3600
        },
        {
            'type': 'CNAME',
            'host': 'autodiscover',
            'value': 'autodiscover.outlook.com',
            'ttl': 3600
        },
        {
            'type': 'CNAME',
            'host': 'enterpriseregistration',
            'value': 'enterpriseregistration.windows.net',
            'ttl': 3600
        }
    ]


@pytest.fixture
def sample_namecheap_private_email_records():
    """Sample NameCheap Private Email DNS records"""
    return [
        {
            'type': 'A',
            'host': '@',
            'value': 'your-server-ip',
            'ttl': 1800
        },
        {
            'type': 'MX',
            'host': '@',
            'value': 'mx1.privateemail.com',
            'priority': 10,
            'ttl': 3600
        },
        {
            'type': 'MX',
            'host': '@',
            'value': 'mx2.privateemail.com',
            'priority': 10,
            'ttl': 3600
        },
        {
            'type': 'TXT',
            'host': '@',
            'value': 'v=spf1 include:spf.privateemail.com -all',
            'ttl': 3600
        },
        {
            'type': 'CNAME',
            'host': 'autoconfig',
            'value': 'autoconfig.privateemail.com',
            'ttl': 3600
        }
    ]


@pytest.fixture
def sample_google_workspace_records():
    """Sample Google Workspace email DNS records"""
    return [
        {
            'type': 'MX',
            'host': '@',
            'value': 'aspmx.l.google.com',
            'priority': 1,
            'ttl': 3600
        },
        {
            'type': 'MX',
            'host': '@',
            'value': 'alt1.aspmx.l.google.com',
            'priority': 5,
            'ttl': 3600
        },
        {
            'type': 'MX',
            'host': '@',
            'value': 'alt2.aspmx.l.google.com',
            'priority': 5,
            'ttl': 3600
        },
        {
            'type': 'TXT',
            'host': '@',
            'value': 'v=spf1 include:_spf.google.com ~all',
            'ttl': 3600
        },
        {
            'type': 'TXT',
            'host': 'google._domainkey',
            'value': 'v=DKIM1; k=rsa; p=MIGfMA0GCSqGSIb3...',
            'ttl': 3600
        }
    ]


@pytest.fixture
def sample_all_record_types():
    """Sample DNS records with all supported types"""
    return [
        {'type': 'A', 'host': '@', 'value': 'your-server-ip', 'ttl': 1800},
        {'type': 'AAAA', 'host': '@', 'value': '2606:4700:4700::1111', 'ttl': 1800},
        {'type': 'CNAME', 'host': 'www', 'value': 'example.com', 'ttl': 1800},
        {'type': 'MX', 'host': '@', 'value': 'mail.example.com', 'priority': 10, 'ttl': 3600},
        {'type': 'TXT', 'host': '@', 'value': 'v=spf1 include:example.com -all', 'ttl': 3600},
        {'type': 'SRV', 'host': '_service._tcp', 'value': 'server.example.com', 'priority': 10, 'weight': 5, 'port': 443, 'ttl': 3600},
        {'type': 'CAA', 'host': '@', 'value': '0 issue "letsencrypt.org"', 'flags': 0, 'tag': 'issue', 'ttl': 3600},
        {'type': 'NS', 'host': 'subdomain', 'value': 'ns1.example.com', 'ttl': 3600}
    ]


# ============================================================================
# Email Service Detection Fixtures
# ============================================================================

@pytest.fixture
def detected_microsoft365_service():
    """Detected Microsoft 365 email service"""
    return {
        'domain': 'unicorncommander.ai',
        'service_type': 'microsoft365',
        'detected_at': datetime.now().isoformat(),
        'mx_records': ['superiorbsolutions-com.mail.protection.outlook.com'],
        'spf_record': 'v=spf1 include:spf.protection.outlook.com -all',
        'dmarc_record': 'v=DMARC1; p=none; rua=mailto:dmarc@example.com',
        'dkim_selectors': [],
        'additional_records': [
            {'type': 'CNAME', 'host': 'autodiscover', 'value': 'autodiscover.outlook.com'},
            {'type': 'CNAME', 'host': 'enterpriseregistration', 'value': 'enterpriseregistration.windows.net'}
        ],
        'preserved': True
    }


@pytest.fixture
def detected_namecheap_private_email():
    """Detected NameCheap Private Email service"""
    return {
        'domain': 'magicunicorn.tech',
        'service_type': 'namecheap_private',
        'detected_at': datetime.now().isoformat(),
        'mx_records': ['mx1.privateemail.com', 'mx2.privateemail.com'],
        'spf_record': 'v=spf1 include:spf.privateemail.com -all',
        'dmarc_record': None,
        'dkim_selectors': [],
        'additional_records': [
            {'type': 'CNAME', 'host': 'autoconfig', 'value': 'autoconfig.privateemail.com'}
        ],
        'preserved': True
    }


@pytest.fixture
def detected_google_workspace():
    """Detected Google Workspace email service"""
    return {
        'domain': 'example.com',
        'service_type': 'google_workspace',
        'detected_at': datetime.now().isoformat(),
        'mx_records': ['aspmx.l.google.com', 'alt1.aspmx.l.google.com', 'alt2.aspmx.l.google.com'],
        'spf_record': 'v=spf1 include:_spf.google.com ~all',
        'dmarc_record': None,
        'dkim_selectors': ['google'],
        'additional_records': [],
        'preserved': True
    }


# ============================================================================
# Migration Job Fixtures
# ============================================================================

@pytest.fixture
def sample_migration_job():
    """Sample migration job"""
    return {
        'id': '660e8400-e29b-41d4-a716-446655440000',
        'job_name': 'NameCheap to Cloudflare Migration',
        'status': 'pending',
        'started_at': datetime.now().isoformat(),
        'completed_at': None,
        'created_by': 'test_user@example.com',
        'total_domains': 3,
        'completed_domains': 0,
        'failed_domains': 0,
        'queued_domains': 3,
        'estimated_completion': (datetime.now() + timedelta(minutes=30)).isoformat(),
        'metadata': {}
    }


@pytest.fixture
def sample_migration_domain_queue():
    """Sample migration domain queue entries"""
    return [
        {
            'id': '770e8400-e29b-41d4-a716-446655440000',
            'domain': 'unicorncommander.ai',
            'priority': 'high',
            'status': 'queued',
            'phase': 'queued',
            'queue_position': 1,
            'cloudflare_zone_id': None,
            'dns_records_imported': 0,
            'nameservers_updated': False,
            'propagation_percent': 0,
            'attempt_count': 0,
            'last_attempt': None,
            'error_message': None,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'completed_at': None,
            'metadata': {}
        },
        {
            'id': '770e8400-e29b-41d4-a716-446655440001',
            'domain': 'superiorbsolutions.com',
            'priority': 'normal',
            'status': 'queued',
            'phase': 'queued',
            'queue_position': 2,
            'cloudflare_zone_id': None,
            'dns_records_imported': 0,
            'nameservers_updated': False,
            'propagation_percent': 0,
            'attempt_count': 0,
            'last_attempt': None,
            'error_message': None,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'completed_at': None,
            'metadata': {}
        }
    ]


# ============================================================================
# DNS Backup Fixtures
# ============================================================================

@pytest.fixture
def sample_dns_backup():
    """Sample DNS backup"""
    return {
        'id': '880e8400-e29b-41d4-a716-446655440000',
        'domain': 'unicorncommander.ai',
        'exported_at': datetime.now().isoformat(),
        'exported_by': 'test_user@example.com',
        'original_nameservers': ['dns1.registrar-servers.com', 'dns2.registrar-servers.com'],
        'records': [],  # Will be populated by specific tests
        'format': 'json',
        'file_path': '/backups/dns/unicorncommander.ai_20251022_120000.json',
        'retain_until': (datetime.now() + timedelta(days=90)).isoformat()
    }


# ============================================================================
# Cloudflare Mock Fixtures
# ============================================================================

@pytest.fixture
def mock_cloudflare_client():
    """Mock Cloudflare API client"""
    client = Mock()

    client.add_zone = AsyncMock(return_value={
        'success': True,
        'result': {
            'id': 'cf_zone_id_123',
            'name': 'unicorncommander.ai',
            'status': 'pending',
            'nameservers': ['vera.ns.cloudflare.com', 'walt.ns.cloudflare.com']
        }
    })

    client.create_dns_record = AsyncMock(return_value={
        'success': True,
        'result': {
            'id': 'cf_record_id_123',
            'type': 'A',
            'name': '@',
            'content': 'your-server-ip',
            'ttl': 1800
        }
    })

    client.get_zone_status = AsyncMock(return_value={
        'success': True,
        'result': {
            'status': 'active',
            'nameservers': ['vera.ns.cloudflare.com', 'walt.ns.cloudflare.com']
        }
    })

    return client


# ============================================================================
# Health Check Fixtures
# ============================================================================

@pytest.fixture
def sample_health_check_results():
    """Sample health check results"""
    return {
        'domain': 'unicorncommander.ai',
        'check_type': 'full',
        'checked_at': datetime.now().isoformat(),
        'status': 'passed',
        'details': {
            'dns_propagation': {
                'status': 'passed',
                'propagation_percent': 100,
                'resolvers': {
                    'Google DNS (8.8.8.8)': True,
                    'Cloudflare DNS (1.1.1.1)': True,
                    'Quad9 DNS (9.9.9.9)': True,
                    'OpenDNS (208.67.222.222)': True,
                    'Local DNS': True
                }
            },
            'ssl_certificate': {
                'status': 'passed',
                'issued': True,
                'issuer': 'Cloudflare Inc ECC CA-3',
                'valid_from': datetime.now().isoformat(),
                'valid_to': (datetime.now() + timedelta(days=90)).isoformat()
            },
            'email_functionality': {
                'status': 'passed',
                'mx_records': ['superiorbsolutions-com.mail.protection.outlook.com'],
                'spf_configured': True,
                'dmarc_configured': True
            },
            'website_accessibility': {
                'status': 'passed',
                'http': {'status_code': 301, 'redirected_to': 'https://unicorncommander.ai'},
                'https': {'status_code': 200, 'accessible': True}
            }
        }
    }


# ============================================================================
# Error Response Fixtures
# ============================================================================

@pytest.fixture
def namecheap_api_error_responses():
    """Sample NameCheap API error responses"""
    return {
        'domain_locked': {
            'success': False,
            'error': 'Domain is locked',
            'error_code': 'DOMAIN_LOCKED'
        },
        'domain_expired': {
            'success': False,
            'error': 'Domain has expired',
            'error_code': 'DOMAIN_EXPIRED'
        },
        'rate_limit': {
            'success': False,
            'error': 'API rate limit exceeded',
            'error_code': 'RATE_LIMIT_EXCEEDED'
        },
        'invalid_nameservers': {
            'success': False,
            'error': 'Invalid nameserver format',
            'error_code': 'INVALID_NAMESERVERS'
        },
        'insufficient_permissions': {
            'success': False,
            'error': 'Insufficient permissions',
            'error_code': 'INSUFFICIENT_PERMISSIONS'
        }
    }


# ============================================================================
# Database Mock Fixtures
# ============================================================================

@pytest.fixture
def mock_migration_db():
    """Mock migration database"""
    db = MagicMock()

    # Mock query methods
    db.query = MagicMock(return_value=[])
    db.insert = MagicMock(return_value='new_record_id')
    db.update = MagicMock(return_value=True)
    db.delete = MagicMock(return_value=True)

    return db


# ============================================================================
# Utility Functions
# ============================================================================

def create_mock_response(success: bool, data: Any = None, error: str = None) -> Dict:
    """Helper to create standardized mock API responses"""
    response = {'success': success}
    if data:
        response['result'] = data
    if error:
        response['error'] = error
    return response
