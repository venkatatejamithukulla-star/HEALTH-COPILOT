"""
HealthMate AI - Security Module (SPEC.md Phase 1)
Implements:
- 14b: AES-256-GCM field-level encryption with key management
- 14b: bcrypt password hashing
- 14b: Aadhaar SHA-256 hashing and last-4 extraction
- 14e: File upload safety validation (blocking .exe, .html, scripts)
"""

import os
import re
import base64
import hashlib
from typing import Optional, Tuple
from pathlib import Path
import bcrypt
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from werkzeug.utils import secure_filename

# Default development fallback key (32 bytes / 256 bits)
DEFAULT_DEV_KEY = b"HealthMateAI_256BitKey_2026_SecureDevKey!"[:32]

def get_encryption_key() -> bytes:
    """
    Retrieves the 256-bit AES encryption key from environment variable HEALTHMATE_ENCRYPTION_KEY,
    falling back to SECRET_KEY derivation or DEFAULT_DEV_KEY.
    """
    raw_key = os.getenv("HEALTHMATE_ENCRYPTION_KEY")
    if raw_key:
        raw_key = raw_key.strip()
        # If hex encoded (64 chars)
        if len(raw_key) == 64:
            try:
                return bytes.fromhex(raw_key)
            except ValueError:
                pass
        # If base64 encoded
        try:
            decoded = base64.b64decode(raw_key)
            if len(decoded) == 32:
                return decoded
        except Exception:
            pass
        # If raw string, derive 32-byte key using SHA-256
        return hashlib.sha256(raw_key.encode("utf-8")).digest()

    secret = os.getenv("SECRET_KEY", "healthmate-dev-secret-key-2026")
    return hashlib.sha256(secret.encode("utf-8")).digest()


def encrypt_field(plaintext: Optional[str]) -> Optional[str]:
    """
    Encrypts a sensitive string field using AES-256-GCM.
    Returns versioned base64 payload: 'v1:<base64_encoded(nonce + ciphertext + tag)>'.
    """
    if plaintext is None:
        return None
    if not isinstance(plaintext, str):
        plaintext = str(plaintext)
    if plaintext == "":
        return ""

    key = get_encryption_key()
    aesgcm = AESGCM(key)
    # 12-byte nonce for GCM
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    payload = nonce + ciphertext
    return f"v1:{base64.b64encode(payload).decode('ascii')}"


def decrypt_field(encrypted_str: Optional[str]) -> Optional[str]:
    """
    Decrypts an AES-256-GCM encrypted string.
    Expects payload: 'v1:<base64_encoded(nonce + ciphertext + tag)>'.
    """
    if encrypted_str is None:
        return None
    if not isinstance(encrypted_str, str) or not encrypted_str:
        return ""

    if not encrypted_str.startswith("v1:"):
        # Not encrypted with v1 scheme
        return encrypted_str

    b64_part = encrypted_str[3:]
    try:
        raw = base64.b64decode(b64_part)
        if len(raw) < 28: # 12 bytes nonce + 16 bytes tag minimum
            return None
        nonce = raw[:12]
        ciphertext = raw[12:]
        key = get_encryption_key()
        aesgcm = AESGCM(key)
        decrypted = aesgcm.decrypt(nonce, ciphertext, None)
        return decrypted.decode("utf-8")
    except Exception as e:
        # Decryption failed (tampered data or wrong key)
        return None


# ------------------------------------------------------------------------------
# PASSWORD HASHING (bcrypt)
# ------------------------------------------------------------------------------

def hash_password(password: str) -> str:
    """Hashes a password with bcrypt and auto-generated salt."""
    if not password:
        raise ValueError("Password cannot be empty")
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("ascii")


def verify_password(password: str, hashed_password: str) -> bool:
    """Verifies a plain password against stored bcrypt hash."""
    if not password or not hashed_password:
        return False
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("ascii"))
    except Exception:
        return False


# ------------------------------------------------------------------------------
# AADHAAR HASHING & LAST-4 MASKING (14b)
# ------------------------------------------------------------------------------

def hash_aadhaar(aadhaar_number: str) -> Tuple[str, str]:
    """
    Normalizes a 12-digit Indian Aadhaar number, computes SHA-256 hash,
    and returns (aadhaar_hash, aadhaar_last4).
    Plaintext Aadhaar is never saved in the database.
    """
    cleaned = re.sub(r"[\s\-]", "", str(aadhaar_number).strip())
    if not (len(cleaned) == 12 and cleaned.isdigit()):
        raise ValueError("Aadhaar must be a 12-digit numeric identifier.")

    last4 = cleaned[-4:]
    # Peppered SHA-256 hash
    pepper = os.getenv("AADHAAR_PEPPER", "HEALTHMATE_AADHAAR_SALT_2026")
    hasher = hashlib.sha256((cleaned + pepper).encode("utf-8"))
    aadhaar_hash = hasher.hexdigest()

    return aadhaar_hash, last4


# ------------------------------------------------------------------------------
# FILE UPLOAD VALIDATION & SECURITY (14e)
# ------------------------------------------------------------------------------

ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg", "txt"}
FORBIDDEN_EXTENSIONS = {
    "exe", "html", "htm", "js", "bat", "cmd", "sh", "php", "vbs",
    "msi", "dll", "com", "scr", "ps1", "jar", "py", "pif", "asp", "aspx"
}

def validate_uploaded_file(file_storage) -> Tuple[bool, str, Optional[str]]:
    """
    Validates uploaded file against security rules:
    - Rejects empty uploads
    - Strictly blocks forbidden extensions (.exe, .html, scripts)
    - Verifies allowed extensions (.pdf, .png, .jpg, .jpeg, .txt)
    - Checks content headers for dangerous payloads (PE executable headers, HTML scripts)
    - Returns (is_valid, message, sanitized_filename)
    """
    if not file_storage or not file_storage.filename:
        return False, "No file selected.", None

    original_filename = file_storage.filename.strip()
    safe_name = secure_filename(original_filename)
    if not safe_name:
        return False, "Invalid filename.", None

    # Check extension
    if "." not in safe_name:
        return False, "File must have a valid extension.", None

    ext = safe_name.rsplit(".", 1)[-1].lower()

    if ext in FORBIDDEN_EXTENSIONS:
        return False, f"File type '.{ext}' is strictly prohibited for security reasons.", None

    if ext not in ALLOWED_EXTENSIONS:
        return False, f"Unsupported file type. Only PDF, JPG, PNG, and TXT are permitted.", None

    # Content inspection on initial bytes
    try:
        header = file_storage.read(512)
        file_storage.seek(0) # Reset stream position

        # Check for Windows PE executable header (MZ)
        if header.startswith(b"MZ"):
            return False, "Dangerous executable payload detected.", None

        # Check for HTML/script tags disguised as other formats
        header_lower = header.lower()
        if b"<html" in header_lower or b"<script" in header_lower or b"<?php" in header_lower:
            return False, "Executable script/HTML content detected.", None

    except Exception as e:
        return False, f"File verification error: {str(e)}", None

    return True, "File verified successfully.", safe_name
