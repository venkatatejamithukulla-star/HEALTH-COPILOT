"""
HealthMate AI - ORM Models (SPEC.md Phase 1)
Implements:
- users table (14b, 14c): bcrypt, roles, lockout after 5 attempts, Aadhaar hash + last 4
- profiles table (14b, 14c): user ownership check, AES-256-GCM encrypted medical notes & contact
- audit_log table (14c): immutable security audit trail
- consents table (14a): disclaimer & privacy acceptance tracking
- user_sessions table (14c): session tracking and auto-logout
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Index

import security

db = SQLAlchemy()

class User(db.Model):
    """
    User Account model.
    Supports email/password or mobile login, role-based authorization,
    lockout after 5 failed login attempts, and privacy-preserving Aadhaar hashing.
    """
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, index=True, nullable=True)
    mobile = db.Column(db.String(20), unique=True, index=True, nullable=True)
    password_hash = db.Column(db.String(255), nullable=True)
    role = db.Column(db.String(50), default="patient", nullable=False) # 'patient', 'doctor', 'admin'
    aadhaar_hash = db.Column(db.String(64), nullable=True) # SHA-256 hash of Aadhaar
    aadhaar_last4 = db.Column(db.String(4), nullable=True) # Last 4 digits only
    failed_login_attempts = db.Column(db.Integer, default=0, nullable=False)
    is_locked = db.Column(db.Boolean, default=False, nullable=False)
    locked_at = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    profiles = db.relationship("Profile", backref="user", lazy=True, cascade="all, delete-orphan")
    audit_logs = db.relationship("AuditLog", backref="user", lazy=True)
    consents = db.relationship("Consent", backref="user", lazy=True, cascade="all, delete-orphan")
    sessions = db.relationship("UserSession", backref="user", lazy=True, cascade="all, delete-orphan")

    def set_password(self, password: str):
        self.password_hash = security.hash_password(password)

    def check_password(self, password: str) -> bool:
        if not self.password_hash:
            return False
        return security.verify_password(password, self.password_hash)

    def register_failed_login(self, max_attempts: int = 5):
        """Increments failed attempts and locks account if threshold reached."""
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= max_attempts:
            self.is_locked = True
            self.locked_at = datetime.utcnow()
        db.session.commit()

    def reset_failed_logins(self):
        """Resets failed login counter upon successful authentication."""
        self.failed_login_attempts = 0
        self.is_locked = False
        self.locked_at = None
        db.session.commit()

    def set_aadhaar(self, aadhaar_number: str):
        """Computes hash and stores only hash and last 4 digits."""
        ahash, last4 = security.hash_aadhaar(aadhaar_number)
        self.aadhaar_hash = ahash
        self.aadhaar_last4 = last4

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "email": self.email,
            "mobile": self.mobile,
            "role": self.role,
            "aadhaar_last4": self.aadhaar_last4,
            "is_locked": self.is_locked,
            "failed_login_attempts": self.failed_login_attempts,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class Profile(db.Model):
    """
    Family Member Profile model.
    Enforces user_id ownership check on every query.
    Sensitive medical notes and emergency contact numbers are encrypted with AES-256-GCM.
    """
    __tablename__ = "profiles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    relationship = db.Column(db.String(50), default="Self", nullable=False)
    age = db.Column(db.Integer, nullable=True)
    gender = db.Column(db.String(20), nullable=True)
    blood_group = db.Column(db.String(10), nullable=True)
    is_default = db.Column(db.Boolean, default=False, nullable=False)

    # 14b Encrypted fields (AES-256-GCM ciphertext)
    emergency_contact_encrypted = db.Column(db.Text, nullable=True)
    medical_notes_encrypted = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def set_emergency_contact(self, plain_text: Optional[str]):
        self.emergency_contact_encrypted = security.encrypt_field(plain_text)

    def get_emergency_contact(self) -> Optional[str]:
        return security.decrypt_field(self.emergency_contact_encrypted)

    def set_medical_notes(self, plain_text: Optional[str]):
        self.medical_notes_encrypted = security.encrypt_field(plain_text)

    def get_medical_notes(self) -> Optional[str]:
        return security.decrypt_field(self.medical_notes_encrypted)

    def to_dict(self, include_decrypted: bool = True) -> Dict[str, Any]:
        data = {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "relationship": self.relationship,
            "age": self.age,
            "gender": self.gender,
            "blood_group": self.blood_group,
            "is_default": self.is_default,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
        if include_decrypted:
            data["emergency_contact"] = self.get_emergency_contact()
            data["medical_notes"] = self.get_medical_notes()
        else:
            data["emergency_contact_encrypted"] = self.emergency_contact_encrypted
            data["medical_notes_encrypted"] = self.medical_notes_encrypted
        return data


class AuditLog(db.Model):
    """
    Immutable Security and Access Audit Log (14c).
    Records authentication events, data accesses, and ownership violations.
    """
    __tablename__ = "audit_log"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action = db.Column(db.String(100), nullable=False, index=True)
    resource_type = db.Column(db.String(50), nullable=True)
    resource_id = db.Column(db.String(50), nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)
    details = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    @classmethod
    def log(cls, action: str, user_id: Optional[int] = None, resource_type: Optional[str] = None,
            resource_id: Optional[str] = None, ip_address: Optional[str] = None,
            user_agent: Optional[str] = None, details: Optional[str] = None) -> "AuditLog":
        entry = cls(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details,
            created_at=datetime.utcnow()
        )
        db.session.add(entry)
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
        return entry

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "ip_address": self.ip_address,
            "details": self.details,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class Consent(db.Model):
    """
    Consent and Disclaimer records (14a).
    Tracks user consent for Disclaimers, Terms of Service, and Privacy Policy.
    """
    __tablename__ = "consents"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    consent_type = db.Column(db.String(100), default="disclaimer_terms", nullable=False)
    version = db.Column(db.String(20), default="1.0", nullable=False)
    is_accepted = db.Column(db.Boolean, default=True, nullable=False)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)
    accepted_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    @classmethod
    def has_accepted(cls, user_id: int, consent_type: str = "disclaimer_terms", version: str = "1.0") -> bool:
        record = cls.query.filter_by(
            user_id=user_id,
            consent_type=consent_type,
            version=version,
            is_accepted=True
        ).first()
        return record is not None

    @classmethod
    def record_consent(cls, user_id: int, consent_type: str = "disclaimer_terms",
                       version: str = "1.0", ip_address: Optional[str] = None,
                       user_agent: Optional[str] = None) -> "Consent":
        existing = cls.query.filter_by(
            user_id=user_id,
            consent_type=consent_type,
            version=version
        ).first()
        if existing:
            existing.is_accepted = True
            existing.accepted_at = datetime.utcnow()
            existing.ip_address = ip_address
            existing.user_agent = user_agent
            consent = existing
        else:
            consent = cls(
                user_id=user_id,
                consent_type=consent_type,
                version=version,
                is_accepted=True,
                ip_address=ip_address,
                user_agent=user_agent,
                accepted_at=datetime.utcnow()
            )
            db.session.add(consent)
        db.session.commit()
        return consent


class UserSession(db.Model):
    """
    Active User Session Tracking (14c).
    Enforces session timeout / auto-logout and concurrent session visibility.
    """
    __tablename__ = "user_sessions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    session_token = db.Column(db.String(128), unique=True, index=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    last_activity = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)

    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at or not self.is_active

    def touch(self, extension_minutes: int = 30):
        self.last_activity = datetime.utcnow()
        self.expires_at = datetime.utcnow() + timedelta(minutes=extension_minutes)
        db.session.commit()
