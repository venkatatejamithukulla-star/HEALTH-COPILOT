"""
HealthMate AI - Authentication, Authorization & Ownership Module (SPEC.md Phase 1)
Implements:
- 14a: Mandatory Disclaimers, Terms, Privacy Policy & Consent enforcement
- 14c: Patient login (Email+Password and Mobile OTP), 5-failure lockout, roles,
       ownership check on every query, auto-logout, active session management
"""

import os
import secrets
from datetime import datetime, timedelta
from functools import wraps
from typing import Optional, Dict, Any
from flask import Blueprint, request, session, jsonify, g, current_app

from models import db, User, Profile, AuditLog, Consent, UserSession
import security

auth_bp = Blueprint("auth", __name__)

# Temporary in-memory OTP storage for prototype testing {mobile: {"otp": code, "expires_at": time, "attempts": n}}
_OTP_STORE: Dict[str, Dict[str, Any]] = {}

def get_client_ip() -> str:
    """Safely extracts client IP address."""
    return request.headers.get("X-Forwarded-For", request.remote_addr or "127.0.0.1").split(",")[0].strip()


def get_current_user() -> Optional[User]:
    """Retrieves authenticated user from session or active token."""
    if hasattr(g, "current_user") and g.current_user is not None:
        return g.current_user

    user_id = session.get("user_id")
    token = session.get("session_token") or request.headers.get("X-Session-Token")

    if not user_id:
        g.current_user = None
        return None

    # Check active session in DB
    user = User.query.get(user_id)
    if not user or not user.is_active or user.is_locked:
        g.current_user = None
        return None

    if token:
        user_sess = UserSession.query.filter_by(user_id=user.id, session_token=token, is_active=True).first()
        if not user_sess or user_sess.is_expired():
            # Session expired
            session.pop("user_id", None)
            session.pop("session_token", None)
            g.current_user = None
            return None
        user_sess.touch(extension_minutes=30)

    g.current_user = user
    return user


def login_required(f):
    """Decorator requiring a logged-in active user."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if not user:
            return jsonify({
                "success": False,
                "error": "Authentication required. Please log in.",
                "code": "AUTH_REQUIRED"
            }), 401
        return f(*args, **kwargs)
    return decorated_function


def role_required(*allowed_roles):
    """Decorator requiring specific role(s) (e.g., patient, doctor, admin)."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = get_current_user()
            if not user:
                return jsonify({"success": False, "error": "Authentication required."}), 401
            if user.role not in allowed_roles:
                AuditLog.log(
                    action="ROLE_UNAUTHORIZED",
                    user_id=user.id,
                    ip_address=get_client_ip(),
                    details=f"User role '{user.role}' attempted action requiring {allowed_roles}"
                )
                return jsonify({
                    "success": False,
                    "error": f"Forbidden: Action requires one of roles: {', '.join(allowed_roles)}.",
                    "code": "FORBIDDEN_ROLE"
                }), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def require_consent(consent_type="disclaimer_terms", version="1.0"):
    """
    Decorator enforcing that user has accepted mandatory medical disclaimer / terms.
    If not accepted, blocks request with 403 and requires_consent flag.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = get_current_user()
            if not user:
                return jsonify({"success": False, "error": "Authentication required."}), 401

            has_accepted = Consent.has_accepted(user.id, consent_type=consent_type, version=version)
            if not has_accepted:
                AuditLog.log(
                    action="CONSENT_REQUIRED_BLOCKED",
                    user_id=user.id,
                    ip_address=get_client_ip(),
                    details=f"Blocked access because consent '{consent_type}' version '{version}' not accepted."
                )
                return jsonify({
                    "success": False,
                    "error": "Mandatory medical disclaimer and terms must be accepted before accessing health services.",
                    "requires_consent": True,
                    "consent_type": consent_type,
                    "version": version
                }), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# ------------------------------------------------------------------------------
# AUTHENTICATION ROUTES (14c)
# ------------------------------------------------------------------------------

@auth_bp.route("/api/auth/register", methods=["POST"])
def register():
    """Registers a new user account with bcrypt password and optional Aadhaar hash."""
    data = request.get_json() or {}
    email = data.get("email", "").strip().lower() or None
    mobile = data.get("mobile", "").strip() or None
    password = data.get("password", "")
    role = data.get("role", "patient").strip().lower()
    aadhaar = data.get("aadhaar", "").strip() or None

    if not email and not mobile:
        return jsonify({"success": False, "error": "Email or mobile number is required."}), 400

    if not password or len(password) < 8:
        return jsonify({"success": False, "error": "Password must be at least 8 characters long."}), 400

    if role not in ["patient", "doctor", "admin"]:
        role = "patient"

    # Check uniqueness
    if email and User.query.filter_by(email=email).first():
        return jsonify({"success": False, "error": "An account with this email already exists."}), 400
    if mobile and User.query.filter_by(mobile=mobile).first():
        return jsonify({"success": False, "error": "An account with this mobile already exists."}), 400

    new_user = User(
        email=email,
        mobile=mobile,
        role=role,
        is_active=True,
        failed_login_attempts=0,
        is_locked=False
    )
    new_user.set_password(password)

    if aadhaar:
        try:
            new_user.set_aadhaar(aadhaar)
        except ValueError as ve:
            return jsonify({"success": False, "error": str(ve)}), 400

    db.session.add(new_user)
    db.session.commit()

    # Automatically create a default self profile
    default_profile = Profile(
        user_id=new_user.id,
        name=email.split("@")[0].title() if email else f"User {mobile[-4:]}",
        relationship="Self",
        is_default=True
    )
    db.session.add(default_profile)
    db.session.commit()

    AuditLog.log(
        action="USER_REGISTERED",
        user_id=new_user.id,
        ip_address=get_client_ip(),
        user_agent=request.user_agent.string,
        details=f"Registered user ID {new_user.id} with role '{role}'"
    )

    return jsonify({
        "success": True,
        "message": "User registered successfully.",
        "user": new_user.to_dict()
    }), 201


@auth_bp.route("/api/auth/login", methods=["POST"])
def login():
    """
    User login via email or mobile and password.
    Enforces 5-failure account lockout (14c).
    """
    data = request.get_json() or {}
    identifier = data.get("identifier", "").strip().lower()
    password = data.get("password", "")

    if not identifier or not password:
        return jsonify({"success": False, "error": "Identifier (email/mobile) and password are required."}), 400

    # Locate user by email or mobile
    user = User.query.filter((User.email == identifier) | (User.mobile == identifier)).first()

    if not user:
        AuditLog.log(
            action="LOGIN_UNKNOWN_IDENTIFIER",
            ip_address=get_client_ip(),
            details=f"Failed login attempt for nonexistent identifier: {identifier}"
        )
        return jsonify({"success": False, "error": "Invalid identifier or password."}), 401

    # Check if account is locked
    if user.is_locked:
        AuditLog.log(
            action="LOGIN_ATTEMPT_ON_LOCKED_ACCOUNT",
            user_id=user.id,
            ip_address=get_client_ip(),
            details=f"User {user.id} attempted login while account is locked."
        )
        return jsonify({
            "success": False,
            "error": "Account is locked due to 5 consecutive failed login attempts. Please contact support.",
            "is_locked": True,
            "failed_attempts": user.failed_login_attempts
        }), 423 # 423 Locked

    # Verify password
    if not user.check_password(password):
        user.register_failed_login(max_attempts=5)
        AuditLog.log(
            action="LOGIN_FAILED",
            user_id=user.id,
            ip_address=get_client_ip(),
            details=f"Password failure. Attempt {user.failed_login_attempts}/5"
        )
        if user.is_locked:
            AuditLog.log(
                action="ACCOUNT_LOCKED",
                user_id=user.id,
                ip_address=get_client_ip(),
                details=f"Account locked after {user.failed_login_attempts} failed attempts."
            )
            return jsonify({
                "success": False,
                "error": "Account has been locked due to 5 consecutive failed login attempts.",
                "is_locked": True,
                "failed_attempts": user.failed_login_attempts
            }), 423

        remaining = 5 - user.failed_login_attempts
        return jsonify({
            "success": False,
            "error": f"Invalid password. {remaining} attempt(s) remaining before lockout.",
            "failed_attempts": user.failed_login_attempts
        }), 401

    # Authentication successful
    user.reset_failed_logins()

    # Create active session
    token = secrets.token_hex(32)
    new_sess = UserSession(
        user_id=user.id,
        session_token=token,
        expires_at=datetime.utcnow() + timedelta(minutes=30),
        ip_address=get_client_ip(),
        user_agent=request.user_agent.string
    )
    db.session.add(new_sess)
    db.session.commit()

    session["user_id"] = user.id
    session["session_token"] = token
    g.current_user = user

    AuditLog.log(
        action="LOGIN_SUCCESS",
        user_id=user.id,
        ip_address=get_client_ip(),
        details=f"Successful login for user ID {user.id}"
    )

    # Check if disclaimer is accepted
    has_disclaimer = Consent.has_accepted(user.id, consent_type="disclaimer_terms")

    return jsonify({
        "success": True,
        "message": "Login successful.",
        "user": user.to_dict(),
        "session_token": token,
        "disclaimer_accepted": has_disclaimer
    })


@auth_bp.route("/api/auth/otp/send", methods=["POST"])
def send_otp():
    """Generates a test 6-digit OTP for mobile verification (prototype simulation)."""
    data = request.get_json() or {}
    mobile = data.get("mobile", "").strip()

    if not mobile or len(mobile) < 10:
        return jsonify({"success": False, "error": "Valid 10-digit mobile number required."}), 400

    otp_code = f"{secrets.randbelow(900000) + 100000}"
    _OTP_STORE[mobile] = {
        "otp": otp_code,
        "expires_at": datetime.utcnow() + timedelta(minutes=5),
        "attempts": 0
    }

    AuditLog.log(
        action="OTP_GENERATED",
        ip_address=get_client_ip(),
        details=f"Generated OTP for mobile {mobile[-4:]}"
    )

    return jsonify({
        "success": True,
        "message": "OTP sent successfully to mobile.",
        "mobile": mobile,
        # Prototype helper returned for test verification
        "_prototype_otp": otp_code
    })


@auth_bp.route("/api/auth/otp/verify", methods=["POST"])
def verify_otp():
    """Verifies mobile OTP and logs in / registers the user."""
    data = request.get_json() or {}
    mobile = data.get("mobile", "").strip()
    otp_code = data.get("otp", "").strip()

    if not mobile or not otp_code:
        return jsonify({"success": False, "error": "Mobile and OTP are required."}), 400

    record = _OTP_STORE.get(mobile)
    if not record or datetime.utcnow() > record["expires_at"]:
        return jsonify({"success": False, "error": "OTP expired or not found. Please request a new one."}), 400

    if record["otp"] != otp_code:
        record["attempts"] += 1
        if record["attempts"] >= 5:
            _OTP_STORE.pop(mobile, None)
            return jsonify({"success": False, "error": "Too many invalid OTP attempts. Blocked."}), 423
        return jsonify({"success": False, "error": "Incorrect OTP."}), 400

    # Clean OTP once used
    _OTP_STORE.pop(mobile, None)

    # Find or auto-create patient account
    user = User.query.filter_by(mobile=mobile).first()
    if not user:
        user = User(
            mobile=mobile,
            role="patient",
            is_active=True
        )
        db.session.add(user)
        db.session.commit()

        default_profile = Profile(
            user_id=user.id,
            name=f"User {mobile[-4:]}",
            relationship="Self",
            is_default=True
        )
        db.session.add(default_profile)
        db.session.commit()

    token = secrets.token_hex(32)
    new_sess = UserSession(
        user_id=user.id,
        session_token=token,
        expires_at=datetime.utcnow() + timedelta(minutes=30),
        ip_address=get_client_ip(),
        user_agent=request.user_agent.string
    )
    db.session.add(new_sess)
    db.session.commit()

    session["user_id"] = user.id
    session["session_token"] = token
    g.current_user = user

    AuditLog.log(
        action="LOGIN_OTP_SUCCESS",
        user_id=user.id,
        ip_address=get_client_ip(),
        details=f"User ID {user.id} logged in via mobile OTP"
    )

    return jsonify({
        "success": True,
        "message": "OTP verified successfully. Logged in.",
        "user": user.to_dict(),
        "session_token": token,
        "disclaimer_accepted": Consent.has_accepted(user.id, "disclaimer_terms")
    })


@auth_bp.route("/api/auth/logout", methods=["POST"])
@login_required
def logout():
    """Logs out current user, revokes active session token."""
    user = get_current_user()
    token = session.get("session_token")
    if token and user:
        UserSession.query.filter_by(user_id=user.id, session_token=token).update({"is_active": False})
        db.session.commit()

    AuditLog.log(
        action="LOGOUT",
        user_id=user.id if user else None,
        ip_address=get_client_ip(),
        details="User logged out."
    )

    session.pop("user_id", None)
    session.pop("session_token", None)
    g.current_user = None

    return jsonify({"success": True, "message": "Logged out successfully."})


@auth_bp.route("/api/auth/sessions", methods=["GET"])
@login_required
def get_sessions():
    """Returns active sessions for the current authenticated user."""
    user = get_current_user()
    sessions = UserSession.query.filter_by(user_id=user.id, is_active=True).all()
    now = datetime.utcnow()
    active_list = []
    for s in sessions:
        if s.expires_at > now:
            active_list.append({
                "id": s.id,
                "created_at": s.created_at.isoformat(),
                "expires_at": s.expires_at.isoformat(),
                "ip_address": s.ip_address,
                "user_agent": s.user_agent
            })
    return jsonify({"success": True, "sessions": active_list, "total": len(active_list)})


# ------------------------------------------------------------------------------
# CONSENT & DISCLAIMER ROUTES (14a)
# ------------------------------------------------------------------------------

@auth_bp.route("/api/consent/status", methods=["GET"])
def consent_status():
    """Checks whether the user has accepted mandatory disclaimers and terms."""
    user = get_current_user()
    if not user:
        # Check session fallback for anonymous preview
        accepted = session.get("disclaimer_accepted", False)
        return jsonify({"success": True, "is_accepted": bool(accepted), "user_id": None})

    accepted = Consent.has_accepted(user.id, consent_type="disclaimer_terms")
    return jsonify({
        "success": True,
        "is_accepted": accepted,
        "user_id": user.id,
        "disclaimer": "HealthMate AI is an educational health literacy tool. It does not provide clinical diagnosis or dosage alterations."
    })


@auth_bp.route("/api/consent", methods=["POST"])
def record_consent():
    """
    Records user acceptance of Disclaimers, Terms, and Privacy Policy (14a).
    """
    data = request.get_json() or {}
    consent_type = data.get("consent_type", "disclaimer_terms").strip()
    version = data.get("version", "1.0").strip()

    user = get_current_user()
    user_id = user.id if user else session.get("user_id")

    if not user_id:
        # If user is not yet logged in, record in session
        session["disclaimer_accepted"] = True
        return jsonify({
            "success": True,
            "message": "Disclaimer accepted for current session.",
            "is_accepted": True
        })

    consent_record = Consent.record_consent(
        user_id=user_id,
        consent_type=consent_type,
        version=version,
        ip_address=get_client_ip(),
        user_agent=request.user_agent.string
    )

    AuditLog.log(
        action="CONSENT_ACCEPTED",
        user_id=user_id,
        ip_address=get_client_ip(),
        details=f"User accepted consent '{consent_type}' version '{version}'"
    )

    return jsonify({
        "success": True,
        "message": f"Consent for '{consent_type}' recorded successfully.",
        "accepted_at": consent_record.accepted_at.isoformat()
    })


# ------------------------------------------------------------------------------
# OWNERSHIP-PROTECTED PROFILE ROUTES (14c)
# ------------------------------------------------------------------------------

@auth_bp.route("/api/user/profiles", methods=["GET"])
@login_required
@require_consent()
def list_user_profiles():
    """Returns only profiles belonging to the authenticated user."""
    user = get_current_user()
    profiles = Profile.query.filter_by(user_id=user.id).order_by(Profile.is_default.desc(), Profile.id.asc()).all()
    return jsonify({
        "success": True,
        "profiles": [p.to_dict(include_decrypted=True) for p in profiles],
        "total": len(profiles)
    })


@auth_bp.route("/api/user/profiles", methods=["POST"])
@login_required
@require_consent()
def create_user_profile():
    """Creates a new profile owned by the authenticated user with encrypted fields."""
    user = get_current_user()
    data = request.get_json() or {}
    name = data.get("name", "").strip()
    relationship = data.get("relationship", "Self").strip()
    age = data.get("age")
    gender = data.get("gender")
    blood_group = data.get("blood_group")
    emergency_contact = data.get("emergency_contact", "")
    medical_notes = data.get("medical_notes", "")

    if not name:
        return jsonify({"success": False, "error": "Profile name is required."}), 400

    profile = Profile(
        user_id=user.id,
        name=name,
        relationship=relationship,
        age=int(age) if str(age).isdigit() else None,
        gender=gender,
        blood_group=blood_group,
        is_default=False
    )
    if emergency_contact:
        profile.set_emergency_contact(emergency_contact)
    if medical_notes:
        profile.set_medical_notes(medical_notes)

    db.session.add(profile)
    db.session.commit()

    AuditLog.log(
        action="PROFILE_CREATED",
        user_id=user.id,
        resource_type="profile",
        resource_id=str(profile.id),
        ip_address=get_client_ip(),
        details=f"Created profile ID {profile.id} for user {user.id}"
    )

    return jsonify({
        "success": True,
        "message": f"Profile for {name} created successfully.",
        "profile": profile.to_dict(include_decrypted=True)
    }), 201


@auth_bp.route("/api/user/profiles/<int:profile_id>", methods=["GET"])
@login_required
@require_consent()
def get_user_profile_by_id(profile_id):
    """
    CRITICAL OWNERSHIP CHECK (14c):
    User A CANNOT read User B's profile by tampering with profile_id.
    """
    user = get_current_user()
    profile = Profile.query.get(profile_id)

    if not profile:
        return jsonify({"success": False, "error": "Profile not found."}), 404

    # OWNERSHIP CHECK
    if profile.user_id != user.id:
        AuditLog.log(
            action="UNAUTHORIZED_ID_TAMPERING_ATTEMPT",
            user_id=user.id,
            resource_type="profile",
            resource_id=str(profile_id),
            ip_address=get_client_ip(),
            details=f"User ID {user.id} attempted to read profile {profile_id} owned by user {profile.user_id}!"
        )
        return jsonify({
            "success": False,
            "error": "Forbidden: You do not have permission to access this profile.",
            "code": "OWNERSHIP_VIOLATION"
        }), 403

    AuditLog.log(
        action="PROFILE_ACCESSED",
        user_id=user.id,
        resource_type="profile",
        resource_id=str(profile.id),
        ip_address=get_client_ip()
    )

    return jsonify({
        "success": True,
        "profile": profile.to_dict(include_decrypted=True)
    })


@auth_bp.route("/api/user/profiles/<int:profile_id>", methods=["DELETE"])
@login_required
@require_consent()
def delete_user_profile(profile_id):
    """Deletes profile with ownership verification."""
    user = get_current_user()
    profile = Profile.query.get(profile_id)

    if not profile:
        return jsonify({"success": False, "error": "Profile not found."}), 404

    if profile.user_id != user.id:
        AuditLog.log(
            action="UNAUTHORIZED_DELETE_ATTEMPT",
            user_id=user.id,
            resource_type="profile",
            resource_id=str(profile_id),
            ip_address=get_client_ip(),
            details=f"User ID {user.id} attempted to delete profile {profile_id} owned by {profile.user_id}!"
        )
        return jsonify({
            "success": False,
            "error": "Forbidden: You do not have permission to delete this profile."
        }), 403

    if profile.is_default:
        return jsonify({"success": False, "error": "Cannot delete primary default profile."}), 400

    db.session.delete(profile)
    db.session.commit()

    AuditLog.log(
        action="PROFILE_DELETED",
        user_id=user.id,
        resource_type="profile",
        resource_id=str(profile_id),
        ip_address=get_client_ip()
    )

    return jsonify({"success": True, "message": "Profile deleted successfully."})
