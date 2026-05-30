import base64
import hmac as _hmac_stdlib
import secrets

from cryptography.hazmat.primitives import hashes, hmac, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding as asym_padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import padding

PBKDF2_ITERATIONS: int = 600_000
SALT_SIZE: int = 16
NONCE_SIZE: int = 16
KEY_SIZE: int = 32


def generate_code() -> str:
    return secrets.token_hex(16)


def generate_salt() -> bytes:
    return secrets.token_bytes(SALT_SIZE)


def derive_key(code: str, salt: bytes, iterations: int = PBKDF2_ITERATIONS) -> bytes:
    if not code:
        raise ValueError("code não pode ser vazio")
    if len(salt) != SALT_SIZE:
        raise ValueError(f"salt deve ter {SALT_SIZE} bytes, recebeu {len(salt)}")

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=KEY_SIZE,
        salt=salt,
        iterations=iterations,
    )
    return kdf.derive(code.encode("ascii"))


import json

def encrypt_body(plaintext: str, key: bytes) -> tuple[str, str]:
    if len(key) != KEY_SIZE:
        raise ValueError(f"key deve ter {KEY_SIZE} bytes, recebeu {len(key)}")

    # Wrap in JSON envelope and pad to exactly 4096 bytes to prevent traffic size analysis
    envelope = json.dumps({"body": plaintext})
    envelope_bytes = envelope.encode("utf-8")
    
    FIXED_SIZE = 4096
    if len(envelope_bytes) > FIXED_SIZE:
        raise ValueError(f"Mensagem demasiado longa (máximo permitido é cerca de {FIXED_SIZE - 20} caracteres)")
        
    padded_data = envelope_bytes + b"\x00" * (FIXED_SIZE - len(envelope_bytes))

    nonce = secrets.token_bytes(NONCE_SIZE)
    cipher = Cipher(algorithms.AES(key), modes.CTR(nonce))
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(padded_data) + encryptor.finalize()

    return (
        base64.b64encode(ciphertext).decode("ascii"),
        base64.b64encode(nonce).decode("ascii"),
    )


def decrypt_body(ciphertext_b64: str, key: bytes, nonce_b64: str) -> str:
    if len(key) != KEY_SIZE:
        raise ValueError(f"key deve ter {KEY_SIZE} bytes, recebeu {len(key)}")

    ciphertext = base64.b64decode(ciphertext_b64)
    nonce = base64.b64decode(nonce_b64)

    cipher = Cipher(algorithms.AES(key), modes.CTR(nonce))
    decryptor = cipher.decryptor()
    padded_data = decryptor.update(ciphertext) + decryptor.finalize()

    # Remove trailing null bytes and parse JSON envelope
    envelope_bytes = padded_data.rstrip(b"\x00")
    envelope = json.loads(envelope_bytes.decode("utf-8"))
    return envelope["body"]


def compute_hmac(ciphertext_b64: str, key: bytes) -> str:
    h = hmac.HMAC(key, hashes.SHA256())
    h.update(ciphertext_b64.encode("ascii"))
    return base64.b64encode(h.finalize()).decode("ascii")


def verify_hmac(ciphertext_b64: str, key: bytes, expected_mac_b64: str) -> bool:
    computed = compute_hmac(ciphertext_b64, key)
    return _hmac_stdlib.compare_digest(computed, expected_mac_b64)


def hash_password(password: str) -> tuple[str, str]:
    """Hashes a password for storage using PBKDF2."""
    salt = generate_salt()
    key = derive_key(password, salt)
    return base64.b64encode(key).decode("ascii"), base64.b64encode(salt).decode("ascii")


def generate_rsa_key_pair(key_size: int = 2048) -> tuple[str, str]:
    """Generates an RSA key pair and returns (public_key_pem, private_key_pem)."""
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=key_size,
    )
    public_key = private_key.public_key()

    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("ascii")

    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("ascii")

    return public_pem, private_pem


def encrypt_private_key(private_pem: str, password: str, key_cipher_algo: str = "AES-256-CBC") -> tuple[str, str, str]:
    """Encrypts a PEM private key via AES-256-CBC or AES-256-CTR, padded, using a password-derived key.
    Returns (encrypted_pem_b64, iv_b64, salt_b64)."""
    salt = generate_salt()
    key = derive_key(password, salt)
    iv = secrets.token_bytes(NONCE_SIZE)

    padder = padding.PKCS7(algorithms.AES.block_size).padder()
    padded_data = padder.update(private_pem.encode("utf-8")) + padder.finalize()

    if key_cipher_algo == "AES-256-CTR":
        cipher = Cipher(algorithms.AES(key), modes.CTR(iv))
    else:
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv))

    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(padded_data) + encryptor.finalize()

    return (
        base64.b64encode(ciphertext).decode("ascii"),
        base64.b64encode(iv).decode("ascii"),
        base64.b64encode(salt).decode("ascii")
    )


def decrypt_private_key(encrypted_pem_b64: str, password: str, iv_b64: str, salt_b64: str, key_cipher_algo: str = "AES-256-CBC") -> str:
    """Decrypts a PEM private key via AES-256-CBC or AES-256-CTR, padded, using a password-derived key."""
    ciphertext = base64.b64decode(encrypted_pem_b64)
    iv = base64.b64decode(iv_b64)
    salt = base64.b64decode(salt_b64)
    key = derive_key(password, salt)

    if key_cipher_algo == "AES-256-CTR":
        cipher = Cipher(algorithms.AES(key), modes.CTR(iv))
    else:
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv))

    decryptor = cipher.decryptor()
    padded_data = decryptor.update(ciphertext) + decryptor.finalize()

    unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
    private_pem = unpadder.update(padded_data) + unpadder.finalize()
    return private_pem.decode("utf-8")


def sign_receipt(receipt_text: str, private_pem: str, hash_algo: str = "SHA-256") -> str:
    """Signs receipt text using SHA256/384/512withRSA and returns base64 signature."""
    private_key = serialization.load_pem_private_key(
        private_pem.encode("ascii"),
        password=None
    )
    if hash_algo in ("SHA-384", "SHA384", "SHA384withRSA"):
        chosen_hash = hashes.SHA384()
    elif hash_algo in ("SHA-512", "SHA512", "SHA512withRSA"):
        chosen_hash = hashes.SHA512()
    else:
        chosen_hash = hashes.SHA256()

    signature = private_key.sign(
        receipt_text.encode("utf-8"),
        asym_padding.PKCS1v15(),
        chosen_hash
    )
    return base64.b64encode(signature).decode("ascii")


def verify_receipt_signature(receipt_text: str, signature_b64: str, public_pem: str, hash_algo: str = "SHA-256") -> bool:
    """Verifies a SHA256/384/512withRSA signature."""
    public_key = serialization.load_pem_public_key(public_pem.encode("ascii"))
    signature = base64.b64decode(signature_b64)
    if hash_algo in ("SHA-384", "SHA384", "SHA384withRSA"):
        chosen_hash = hashes.SHA384()
    elif hash_algo in ("SHA-512", "SHA512", "SHA512withRSA"):
        chosen_hash = hashes.SHA512()
    else:
        chosen_hash = hashes.SHA256()
    try:
        public_key.verify(
            signature,
            receipt_text.encode("utf-8"),
            asym_padding.PKCS1v15(),
            chosen_hash
        )
        return True
    except Exception:
        return False


def validate_private_key_matches_public(private_pem: str, public_pem: str) -> bool:
    """Returns True if the private key corresponds to the given public key."""
    private_key = serialization.load_pem_private_key(private_pem.encode("ascii"), password=None)
    derived_public = private_key.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("ascii")
    return derived_public.strip() == public_pem.strip()
