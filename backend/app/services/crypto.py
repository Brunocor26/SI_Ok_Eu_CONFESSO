import base64
import hmac as _hmac_stdlib
import secrets
import json

from cryptography.hazmat.primitives import hashes, hmac, serialization
from cryptography.hazmat.primitives import padding as sym_padding
from cryptography.hazmat.primitives.asymmetric import rsa, padding as asym_padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

PBKDF2_ITERATIONS: int = 600_000
SALT_SIZE: int = 16
NONCE_SIZE: int = 16
KEY_SIZE: int = 32


def generate_code() -> str:
    """
    Apenas a função que gera o código de 16 chars, usamos o secrets, considerado seguro.
    """
    return secrets.token_hex(16)


def generate_salt() -> bytes:
    """
    Gera o salt, essencial para evitar ataques de rainbow tables. Sequencia de bytes aleatoria.
    """
    return secrets.token_bytes(SALT_SIZE)


def derive_key(code: str, salt: bytes, iterations: int = PBKDF2_ITERATIONS) -> bytes:
    """
    Usa o PBKDF2. recebe uma password (code) e combina com o salt, faz um numero de iterações e devolve uma
    key segura para encriptação.
    """
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
    """
    Encripta o corpo da mensagem, ao receber texto e key. Devolve tuplo com
    """
    if len(key) != KEY_SIZE:
        raise ValueError(f"key deve ter {KEY_SIZE} bytes, recebeu {len(key)}")

    # Importante! padding para tamanho 4096 para evitar analise ao olhar.
    envelope = json.dumps({"body": plaintext})
    envelope_bytes = envelope.encode("utf-8")
    
    FIXED_SIZE = 4096
    if len(envelope_bytes) > FIXED_SIZE:
        raise ValueError(f"Mensagem demasiado longa (máximo permitido é cerca de {FIXED_SIZE - 20} caracteres)")
        
    #padding de nulls até chegar ao tamanho maximo
    padded_data = envelope_bytes + b"\x00" * (FIXED_SIZE - len(envelope_bytes))

    #garantir que é unico
    nonce = secrets.token_bytes(NONCE_SIZE)
    #cifra com o AES ! importante: tem de ser simetrico para poder reverter e mostrar msg!!
    cipher = Cipher(algorithms.AES(key), modes.CTR(nonce))
    encryptor = cipher.encryptor()
    #adiciona o padding e manda
    ciphertext = encryptor.update(padded_data) + encryptor.finalize()

    return ( #manda texto cifrado e nonce
        base64.b64encode(ciphertext).decode("ascii"),
        base64.b64encode(nonce).decode("ascii"),
    )


def decrypt_body(ciphertext_b64: str, key: bytes, nonce_b64: str) -> str:
    """
    Desencriptar, ao receber o ciphertext, a key e o nonce.
    """
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


def encrypt_private_key(private_pem: str, password: str, cipher_algo: str = "AES-256-CBC") -> str:
    """Cifra a chave privada PEM com uma chave AES-256 derivada via PBKDF2.

    Requisito do enunciado (ponto 2): "a chave privada é cifrada com uma derivação
    segura da palavra-passe de acesso. A cifra a utilizar é a AES-256-CBC."

    Suporta AES-256-CBC (padrão) e AES-256-CTR (ponto bónus 3).
    Devolve uma string JSON contendo todos os parâmetros necessários para a decifragem no browser.
    """
    salt = generate_salt()             # 16 bytes aleatórios para o PBKDF2
    key  = derive_key(password, salt)  # Chave de 256 bits via PBKDF2-SHA256
    iv   = secrets.token_bytes(16)     # 128-bit IV / nonce
    data = private_pem.encode("utf-8")

    if cipher_algo == "AES-256-CTR":
        cipher_obj = Cipher(algorithms.AES(key), modes.CTR(iv))
        encryptor  = cipher_obj.encryptor()
        ciphertext = encryptor.update(data) + encryptor.finalize()
    else:
        # AES-256-CBC com padding PKCS7 padrão
        padder     = sym_padding.PKCS7(128).padder()
        padded     = padder.update(data) + padder.finalize()
        cipher_obj = Cipher(algorithms.AES(key), modes.CBC(iv))
        encryptor  = cipher_obj.encryptor()
        ciphertext = encryptor.update(padded) + encryptor.finalize()

    return json.dumps({
        "cipher":     cipher_algo,
        "kdf":        "PBKDF2-SHA256",
        "iterations": PBKDF2_ITERATIONS,
        "salt":       base64.b64encode(salt).decode("ascii"),
        "iv":         base64.b64encode(iv).decode("ascii"),
        "ciphertext": base64.b64encode(ciphertext).decode("ascii"),
    })



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



def validate_private_key_matches_public(private_pem: str, public_pem: str) -> bool:
    """Returns True if the private key corresponds to the given public key."""
    private_key = serialization.load_pem_private_key(private_pem.encode("ascii"), password=None)
    derived_public = private_key.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("ascii")
    return derived_public.strip() == public_pem.strip()
