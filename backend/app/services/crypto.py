import base64
import hmac as _hmac_stdlib
import secrets

from cryptography.hazmat.primitives import hashes, hmac
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

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


def encrypt_body(plaintext: str, key: bytes) -> tuple[str, str]:
    if len(key) != KEY_SIZE:
        raise ValueError(f"key deve ter {KEY_SIZE} bytes, recebeu {len(key)}")

    nonce = secrets.token_bytes(NONCE_SIZE)
    cipher = Cipher(algorithms.AES(key), modes.CTR(nonce))
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(plaintext.encode("utf-8")) + encryptor.finalize()

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
    return (decryptor.update(ciphertext) + decryptor.finalize()).decode("utf-8")


def compute_hmac(ciphertext_b64: str, key: bytes) -> str:
    h = hmac.HMAC(key, hashes.SHA256())
    h.update(ciphertext_b64.encode("ascii"))
    return base64.b64encode(h.finalize()).decode("ascii")


def verify_hmac(ciphertext_b64: str, key: bytes, expected_mac_b64: str) -> bool:
    computed = compute_hmac(ciphertext_b64, key)
    return _hmac_stdlib.compare_digest(computed, expected_mac_b64)
