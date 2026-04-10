"""
Módulo de criptografia — OK-Eu-CONFESSO
========================================
Implementa as primitivas criptográficas para cifragem/decifragem de mensagens:

  - Geração do código aleatório de 32 chars hex (código enviado no email)
  - Derivação de chave AES-256 via PBKDF2-SHA256 (a partir do código + salt)
  - Cifragem/decifragem AES-256-CTR do corpo da mensagem
  - HMAC-SHA256 para verificação de integridade do criptograma

Todas as funções são puras (sem estado, sem acesso à BD).
Os valores binários são sempre devolvidos em Base64 para serialização segura.

Referências do enunciado:
  - Código aleatório: 32 chars hexadecimal
  - Derivação: PBKDF2 com 600 000 iterações (conforme schema.sql)
  - Cifra: AES-256-CTR
  - Integridade: HMAC-SHA256 (funcionalidade extra obrigatória)
"""

import base64
import hmac as _hmac_stdlib
import secrets

from cryptography.hazmat.primitives import hashes, hmac
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# ---------------------------------------------------------------------------
# Constantes — alinhadas com schema.sql
# ---------------------------------------------------------------------------

PBKDF2_ITERATIONS: int = 600_000  # iterações mínimas recomendadas (2024)
SALT_SIZE: int = 16               # bytes — 128 bits
NONCE_SIZE: int = 16              # bytes — 128 bits (CTR exige nonce do tamanho do bloco AES)
KEY_SIZE: int = 32                # bytes — 256 bits


# ---------------------------------------------------------------------------
# Geração de aleatoriedade segura
# ---------------------------------------------------------------------------

def generate_code() -> str:
    """Gera um código aleatório de 32 caracteres hexadecimal.

    Usa secrets.token_hex para garantir aleatoriedade criptograficamente segura.
    Este código é incluído no email e usado para derivar a chave AES.

    Returns:
        str: 32 chars hex em minúsculas (e.g. "a3f2...").
    """
    return secrets.token_hex(16)  # 16 bytes → 32 chars hex


def generate_salt() -> bytes:
    """Gera um salt aleatório de 16 bytes para uso em PBKDF2.

    Returns:
        bytes: 16 bytes aleatórios.
    """
    return secrets.token_bytes(SALT_SIZE)


# ---------------------------------------------------------------------------
# Derivação de chave — PBKDF2-SHA256
# ---------------------------------------------------------------------------

def derive_key(code: str, salt: bytes, iterations: int = PBKDF2_ITERATIONS) -> bytes:
    """Deriva uma chave AES-256 a partir do código e salt via PBKDF2-SHA256.

    A função é determinística: o mesmo (code, salt, iterations) produz sempre
    a mesma chave. O destinatário usa o código recebido por email + o salt
    guardado na BD para recuperar a chave e decifrar a mensagem.

    Args:
        code: Código aleatório de 32 chars hex.
        salt: Salt aleatório de 16 bytes (guardado na BD com a mensagem).
        iterations: Número de iterações PBKDF2 (padrão: 600 000).

    Returns:
        bytes: Chave de 32 bytes (256 bits).

    Raises:
        ValueError: Se code for vazio ou salt tiver tamanho incorreto.
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


# ---------------------------------------------------------------------------
# Cifragem / Decifragem — AES-256-CTR
# ---------------------------------------------------------------------------

def encrypt_body(plaintext: str, key: bytes) -> tuple[str, str]:
    """Cifra o corpo da mensagem com AES-256-CTR.

    Gera um nonce único por chamada — nunca reutiliza o mesmo nonce com a
    mesma chave (requisito crítico do modo CTR).

    Args:
        plaintext: Texto limpo a cifrar (UTF-8).
        key: Chave AES de 32 bytes derivada via derive_key().

    Returns:
        Tuplo (ciphertext_b64, nonce_b64) ambos em Base64.

    Raises:
        ValueError: Se a chave não tiver 32 bytes.
    """
    if len(key) != KEY_SIZE:
        raise ValueError(f"key deve ter {KEY_SIZE} bytes, recebeu {len(key)}")

    nonce = secrets.token_bytes(NONCE_SIZE)  # novo nonce a cada cifragem
    cipher = Cipher(algorithms.AES(key), modes.CTR(nonce))
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(plaintext.encode("utf-8")) + encryptor.finalize()

    return (
        base64.b64encode(ciphertext).decode("ascii"),
        base64.b64encode(nonce).decode("ascii"),
    )


def decrypt_body(ciphertext_b64: str, key: bytes, nonce_b64: str) -> str:
    """Decifra o corpo da mensagem com AES-256-CTR.

    IMPORTANTE: Verificar sempre o HMAC com verify_hmac() ANTES de chamar
    esta função — não decifrar dados cuja integridade não foi verificada.

    Args:
        ciphertext_b64: Criptograma em Base64.
        key: Chave AES de 32 bytes (deve ser a mesma usada na cifragem).
        nonce_b64: Nonce em Base64 (devolvido por encrypt_body).

    Returns:
        str: Texto decifrado em UTF-8.

    Raises:
        ValueError: Se a chave não tiver 32 bytes.
    """
    if len(key) != KEY_SIZE:
        raise ValueError(f"key deve ter {KEY_SIZE} bytes, recebeu {len(key)}")

    ciphertext = base64.b64decode(ciphertext_b64)
    nonce = base64.b64decode(nonce_b64)

    cipher = Cipher(algorithms.AES(key), modes.CTR(nonce))
    decryptor = cipher.decryptor()
    plaintext_bytes = decryptor.update(ciphertext) + decryptor.finalize()

    return plaintext_bytes.decode("utf-8")


# ---------------------------------------------------------------------------
# Autenticação de mensagem — HMAC-SHA256
# ---------------------------------------------------------------------------

def compute_hmac(ciphertext_b64: str, key: bytes) -> str:
    """Calcula o HMAC-SHA256 do criptograma para verificação de integridade.

    O HMAC é calculado sobre o criptograma em Base64 (a representação que
    é guardada na BD e enviada no email), não sobre os bytes crus.

    Args:
        ciphertext_b64: Criptograma em Base64 (output de encrypt_body).
        key: Chave HMAC de 32 bytes (a mesma chave AES derivada via derive_key).

    Returns:
        str: MAC em Base64.
    """
    h = hmac.HMAC(key, hashes.SHA256())
    h.update(ciphertext_b64.encode("ascii"))
    return base64.b64encode(h.finalize()).decode("ascii")


def verify_hmac(ciphertext_b64: str, key: bytes, expected_mac_b64: str) -> bool:
    """Verifica o HMAC-SHA256 em tempo constante.

    Usa hmac.compare_digest() para prevenir timing attacks — nunca comparar
    MACs com ==, pois a comparação de strings termina logo no primeiro byte
    diferente, revelando informação sobre o MAC esperado.

    Args:
        ciphertext_b64: Criptograma em Base64.
        key: Chave HMAC de 32 bytes.
        expected_mac_b64: MAC esperado em Base64 (guardado na BD).

    Returns:
        bool: True se o MAC for válido, False se a mensagem foi adulterada.
    """
    computed = compute_hmac(ciphertext_b64, key)
    return _hmac_stdlib.compare_digest(computed, expected_mac_b64)
