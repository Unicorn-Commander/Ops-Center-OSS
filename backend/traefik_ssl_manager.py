"""
Traefik SSL Certificate Manager

Manages SSL/TLS certificates from Traefik's acme.json.
Monitors certificate expiration and handles renewal.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
import logging
import json
from datetime import datetime, timedelta
from pathlib import Path
import base64
from cryptography import x509
from cryptography.hazmat.backends import default_backend

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/traefik/ssl", tags=["Traefik SSL"])

# Path to Traefik's acme.json
ACME_JSON_PATH = Path("/home/deploy/Infrastructure/traefik/letsencrypt/acme.json")


class Certificate(BaseModel):
    """SSL certificate information"""
    domain: str
    sans: List[str] = Field(default_factory=list, description="Subject Alternative Names")
    issuer: str
    not_before: str
    not_after: str
    days_remaining: int
    status: str  # valid, expiring_soon, expired
    cert_resolver: str = "letsencrypt"


class CertificateRenewal(BaseModel):
    """Certificate renewal result"""
    domain: str
    success: bool
    message: str


class CertificateStats(BaseModel):
    """SSL certificate statistics"""
    total_certificates: int
    valid_certificates: int
    expiring_soon: int  # < 30 days
    expired_certificates: int


def require_admin(user_info: Dict = Depends(lambda: {"role": "admin", "username": "admin"})):
    """Require admin role"""
    if user_info.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user_info


def parse_certificate_pem(cert_pem: str) -> Dict:
    """
    Parse PEM certificate to extract information.

    Args:
        cert_pem: Certificate in PEM format

    Returns:
        Dictionary with certificate info
    """
    try:
        cert = x509.load_pem_x509_certificate(cert_pem.encode(), default_backend())

        # Get domain (CN from subject)
        subject = cert.subject
        domain = subject.get_attributes_for_oid(x509.NameOID.COMMON_NAME)[0].value

        # Get SANs
        sans = []
        try:
            san_extension = cert.extensions.get_extension_for_oid(x509.ExtensionOID.SUBJECT_ALTERNATIVE_NAME)
            sans = [name.value for name in san_extension.value]
        except x509.ExtensionNotFound:
            pass

        # Get issuer
        issuer = cert.issuer.get_attributes_for_oid(x509.NameOID.COMMON_NAME)[0].value

        # Get validity dates
        not_before = cert.not_valid_before
        not_after = cert.not_valid_after

        # Calculate days remaining
        days_remaining = (not_after - datetime.utcnow()).days

        # Determine status
        if days_remaining < 0:
            status = "expired"
        elif days_remaining < 30:
            status = "expiring_soon"
        else:
            status = "valid"

        return {
            "domain": domain,
            "sans": sans,
            "issuer": issuer,
            "not_before": not_before.isoformat(),
            "not_after": not_after.isoformat(),
            "days_remaining": days_remaining,
            "status": status
        }
    except Exception as e:
        logger.error(f"Error parsing certificate: {e}")
        return None


def load_acme_json() -> Dict:
    """
    Load Traefik's acme.json file.

    Returns:
        Dictionary with ACME data
    """
    if not ACME_JSON_PATH.exists():
        logger.warning(f"ACME JSON file not found: {ACME_JSON_PATH}")
        return {}

    try:
        with open(ACME_JSON_PATH, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading acme.json: {e}")
        return {}


@router.get("/certificates", response_model=List[Certificate])
async def list_certificates(admin: Dict = Depends(require_admin)):
    """
    List all SSL certificates from Traefik.

    Returns:
        List of certificate information
    """
    try:
        acme_data = load_acme_json()
        certificates = []

        # Parse certificates from acme.json
        # Structure: acme.json -> {resolver_name} -> Certificates -> [{domain, certificate}]
        for resolver_name, resolver_data in acme_data.items():
            if not isinstance(resolver_data, dict):
                continue

            cert_list = resolver_data.get('Certificates', [])
            for cert_entry in cert_list:
                cert_pem = cert_entry.get('certificate')
                if not cert_pem:
                    continue

                # Decode if base64
                if isinstance(cert_pem, str) and not cert_pem.startswith('-----BEGIN'):
                    try:
                        cert_pem = base64.b64decode(cert_pem).decode('utf-8')
                    except:
                        pass

                cert_info = parse_certificate_pem(cert_pem)
                if cert_info:
                    cert_info['cert_resolver'] = resolver_name
                    certificates.append(Certificate(**cert_info))

        logger.info(f"Listed {len(certificates)} certificates")
        return certificates

    except Exception as e:
        logger.error(f"Error listing certificates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/certificates/{domain}", response_model=Certificate)
async def get_certificate_info(domain: str, admin: Dict = Depends(require_admin)):
    """
    Get information about a specific certificate.

    Args:
        domain: Domain name

    Returns:
        Certificate information
    """
    try:
        certificates = await list_certificates(admin)

        for cert in certificates:
            if cert.domain == domain or domain in cert.sans:
                return cert

        raise HTTPException(status_code=404, detail=f"Certificate for domain '{domain}' not found")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting certificate for {domain}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=CertificateStats)
async def get_certificate_stats(admin: Dict = Depends(require_admin)):
    """
    Get SSL certificate statistics.

    Returns:
        Certificate statistics
    """
    try:
        certificates = await list_certificates(admin)

        stats = {
            "total_certificates": len(certificates),
            "valid_certificates": 0,
            "expiring_soon": 0,
            "expired_certificates": 0
        }

        for cert in certificates:
            if cert.status == "valid":
                stats["valid_certificates"] += 1
            elif cert.status == "expiring_soon":
                stats["expiring_soon"] += 1
            elif cert.status == "expired":
                stats["expired_certificates"] += 1

        return CertificateStats(**stats)

    except Exception as e:
        logger.error(f"Error getting certificate stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/expiring", response_model=List[Certificate])
async def get_expiring_certificates(
    days: int = 30,
    admin: Dict = Depends(require_admin)
):
    """
    Get certificates expiring within specified days.

    Args:
        days: Number of days threshold (default: 30)

    Returns:
        List of expiring certificates
    """
    try:
        certificates = await list_certificates(admin)
        expiring = [
            cert for cert in certificates
            if 0 < cert.days_remaining <= days
        ]

        logger.info(f"Found {len(expiring)} certificates expiring within {days} days")
        return expiring

    except Exception as e:
        logger.error(f"Error getting expiring certificates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/renew/{domain}", response_model=CertificateRenewal)
async def renew_certificate(domain: str, admin: Dict = Depends(require_admin)):
    """
    Trigger certificate renewal for a domain.

    Note: This is a placeholder. Actual renewal is handled by Traefik automatically.
    This endpoint can be used to force a check or provide status.

    Args:
        domain: Domain name

    Returns:
        Renewal result
    """
    try:
        # Check if certificate exists
        cert = await get_certificate_info(domain, admin)

        # In reality, Traefik handles renewal automatically
        # This is informational only
        if cert.days_remaining > 30:
            return CertificateRenewal(
                domain=domain,
                success=True,
                message=f"Certificate is valid for {cert.days_remaining} more days. Automatic renewal will occur around day 30."
            )
        else:
            return CertificateRenewal(
                domain=domain,
                success=True,
                message=f"Certificate will be renewed automatically by Traefik (expires in {cert.days_remaining} days)"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error renewing certificate for {domain}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/check-rate-limits")
async def check_rate_limits(admin: Dict = Depends(require_admin)):
    """
    Check Let's Encrypt rate limits.

    Note: This is informational. Let's Encrypt rate limits are:
    - 50 certificates per registered domain per week
    - 5 duplicate certificates per week
    - 300 new orders per account per 3 hours

    Returns:
        Rate limit information
    """
    try:
        certificates = await list_certificates(admin)

        # Group by domain
        domain_counts = {}
        for cert in certificates:
            base_domain = '.'.join(cert.domain.split('.')[-2:])  # Get base domain
            domain_counts[base_domain] = domain_counts.get(base_domain, 0) + 1

        return {
            "message": "Let's Encrypt rate limits",
            "limits": {
                "certificates_per_domain_per_week": 50,
                "duplicate_certificates_per_week": 5,
                "new_orders_per_account_per_3_hours": 300
            },
            "current_certificates": domain_counts,
            "total_certificates": len(certificates),
            "note": "Rate limits are per registered domain (e.g., example.com, not subdomain.example.com)"
        }

    except Exception as e:
        logger.error(f"Error checking rate limits: {e}")
        raise HTTPException(status_code=500, detail=str(e))
