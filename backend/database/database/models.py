"""
SQLAlchemy models for Ops-Center database.

This file defines all database tables using SQLAlchemy ORM.
These models are used by Alembic for auto-generating migrations.
"""

from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Text,
    ForeignKey, Table, JSON, Enum as SQLEnum
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()
metadata = Base.metadata


class OrganizationMemberRole(enum.Enum):
    """Roles for organization members"""
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


class InvitationStatus(enum.Enum):
    """Status of organization invitations"""
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"


class MigrationStatus(enum.Enum):
    """Status of domain migration jobs"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class Organization(Base):
    """Organizations table for multi-tenancy support"""
    __tablename__ = 'organizations'

    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    website = Column(String(512), nullable=True)
    logo_url = Column(String(512), nullable=True)
    max_users = Column(Integer, default=5)
    is_active = Column(Boolean, default=True, index=True)
    settings = Column(JSON, nullable=True)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    members = relationship("OrganizationMember", back_populates="organization", cascade="all, delete-orphan")
    invitations = relationship("OrganizationInvitation", back_populates="organization", cascade="all, delete-orphan")
    api_keys = relationship("APIKey", back_populates="organization", cascade="all, delete-orphan")


class OrganizationMember(Base):
    """Organization members table (many-to-many relationship)"""
    __tablename__ = 'organization_members'

    id = Column(String(36), primary_key=True)
    organization_id = Column(String(36), ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = Column(String(255), nullable=False, index=True)  # Keycloak user ID
    role = Column(SQLEnum(OrganizationMemberRole), nullable=False, default=OrganizationMemberRole.MEMBER)
    is_active = Column(Boolean, default=True)
    joined_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    organization = relationship("Organization", back_populates="members")


class OrganizationInvitation(Base):
    """Organization invitations table"""
    __tablename__ = 'organization_invitations'

    id = Column(String(36), primary_key=True)
    organization_id = Column(String(36), ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False, index=True)
    email = Column(String(255), nullable=False, index=True)
    role = Column(SQLEnum(OrganizationMemberRole), nullable=False, default=OrganizationMemberRole.MEMBER)
    invited_by = Column(String(255), nullable=False)  # Keycloak user ID
    status = Column(SQLEnum(InvitationStatus), nullable=False, default=InvitationStatus.PENDING, index=True)
    token = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    organization = relationship("Organization", back_populates="invitations")


class APIKey(Base):
    """API keys table for user authentication"""
    __tablename__ = 'api_keys'

    id = Column(String(36), primary_key=True)
    organization_id = Column(String(36), ForeignKey('organizations.id', ondelete='CASCADE'), nullable=True, index=True)
    user_id = Column(String(255), nullable=False, index=True)  # Keycloak user ID
    name = Column(String(255), nullable=False)
    key_hash = Column(String(255), nullable=False, unique=True, index=True)
    key_prefix = Column(String(20), nullable=False)  # First few chars for display
    scopes = Column(JSON, nullable=True)  # List of allowed scopes/permissions
    is_active = Column(Boolean, default=True, index=True)
    last_used_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    organization = relationship("Organization", back_populates="api_keys")


class AuditLog(Base):
    """Audit logs table for tracking all system activities"""
    __tablename__ = 'audit_logs'

    id = Column(String(36), primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    user_id = Column(String(255), nullable=True, index=True)  # Keycloak user ID
    organization_id = Column(String(36), nullable=True, index=True)
    action = Column(String(255), nullable=False, index=True)
    resource_type = Column(String(100), nullable=True, index=True)
    resource_id = Column(String(255), nullable=True)
    details = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    status = Column(String(50), nullable=True, index=True)  # success, failure, error
    metadata_json = Column(JSON, nullable=True)


# Epic 1.6: Cloudflare Integration Models

class CloudflareZone(Base):
    """Cloudflare DNS zones table"""
    __tablename__ = 'cloudflare_zones'

    id = Column(String(36), primary_key=True)
    zone_id = Column(String(255), nullable=False, unique=True, index=True)
    zone_name = Column(String(255), nullable=False, index=True)
    account_id = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False, index=True)
    name_servers = Column(JSON, nullable=True)
    created_on = Column(DateTime, nullable=True)
    modified_on = Column(DateTime, nullable=True)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    dns_records = relationship("CloudflareDNSRecord", back_populates="zone", cascade="all, delete-orphan")
    firewall_rules = relationship("CloudflareFirewallRule", back_populates="zone", cascade="all, delete-orphan")


class CloudflareDNSRecord(Base):
    """Cloudflare DNS records table"""
    __tablename__ = 'cloudflare_dns_records'

    id = Column(String(36), primary_key=True)
    zone_id = Column(String(255), ForeignKey('cloudflare_zones.zone_id', ondelete='CASCADE'), nullable=False, index=True)
    record_id = Column(String(255), nullable=False, unique=True, index=True)
    record_type = Column(String(10), nullable=False, index=True)  # A, AAAA, CNAME, etc.
    name = Column(String(255), nullable=False, index=True)
    content = Column(Text, nullable=False)
    proxied = Column(Boolean, default=False)
    ttl = Column(Integer, default=3600)
    priority = Column(Integer, nullable=True)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    zone = relationship("CloudflareZone", back_populates="dns_records")


class CloudflareFirewallRule(Base):
    """Cloudflare firewall rules table"""
    __tablename__ = 'cloudflare_firewall_rules'

    id = Column(String(36), primary_key=True)
    zone_id = Column(String(255), ForeignKey('cloudflare_zones.zone_id', ondelete='CASCADE'), nullable=False, index=True)
    rule_id = Column(String(255), nullable=False, unique=True, index=True)
    rule_name = Column(String(255), nullable=False)
    expression = Column(Text, nullable=False)
    action = Column(String(50), nullable=False)  # block, challenge, allow, etc.
    enabled = Column(Boolean, default=True, index=True)
    priority = Column(Integer, nullable=True)
    description = Column(Text, nullable=True)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    zone = relationship("CloudflareZone", back_populates="firewall_rules")


# Epic 1.7: Domain Migration Models

class MigrationJob(Base):
    """Domain migration jobs table"""
    __tablename__ = 'migration_jobs'

    id = Column(String(36), primary_key=True)
    domain_name = Column(String(255), nullable=False, index=True)
    source_registrar = Column(String(100), nullable=False)  # namecheap, godaddy, etc.
    target_registrar = Column(String(100), nullable=False)
    status = Column(SQLEnum(MigrationStatus), nullable=False, default=MigrationStatus.PENDING, index=True)
    auth_code = Column(String(255), nullable=True)  # EPP/transfer code
    initiated_by = Column(String(255), nullable=False)  # User ID
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    steps = Column(JSON, nullable=True)  # Migration steps and their status
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class NamecheapDomain(Base):
    """Namecheap domain registrations table"""
    __tablename__ = 'namecheap_domains'

    id = Column(String(36), primary_key=True)
    domain_name = Column(String(255), nullable=False, unique=True, index=True)
    domain_id = Column(String(255), nullable=True)
    user_id = Column(String(255), nullable=False, index=True)
    registration_date = Column(DateTime, nullable=True)
    expiration_date = Column(DateTime, nullable=True, index=True)
    auto_renew = Column(Boolean, default=True)
    is_locked = Column(Boolean, default=True)
    whois_guard = Column(Boolean, default=True)
    nameservers = Column(JSON, nullable=True)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class CloudflareDomain(Base):
    """Cloudflare domain registrations table"""
    __tablename__ = 'cloudflare_domains'

    id = Column(String(36), primary_key=True)
    domain_name = Column(String(255), nullable=False, unique=True, index=True)
    domain_id = Column(String(255), nullable=True)
    user_id = Column(String(255), nullable=False, index=True)
    zone_id = Column(String(255), nullable=True)  # Associated Cloudflare zone
    registration_date = Column(DateTime, nullable=True)
    expiration_date = Column(DateTime, nullable=True, index=True)
    auto_renew = Column(Boolean, default=True)
    is_locked = Column(Boolean, default=True)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
