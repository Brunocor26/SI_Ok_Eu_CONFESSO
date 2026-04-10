"""
Testes do módulo de criptografia — OK-Eu-CONFESSO
==================================================
Cobre todas as funções públicas de crypto.py:
  - generate_code, generate_salt
  - derive_key
  - encrypt_body, decrypt_body
  - compute_hmac, verify_hmac
  - fluxo completo de cifragem + MAC + decifragem
"""

import base64
import secrets

import pytest

from app.services.crypto import (
    KEY_SIZE,
    NONCE_SIZE,
    PBKDF2_ITERATIONS,
    SALT_SIZE,
    compute_hmac,
    decrypt_body,
    derive_key,
    encrypt_body,
    generate_code,
    generate_salt,
    verify_hmac,
)


# ---------------------------------------------------------------------------
# generate_code
# ---------------------------------------------------------------------------

def test_generate_code_format():
    code = generate_code()
    assert len(code) == 32
    assert all(c in "0123456789abcdef" for c in code)


def test_generate_code_uniqueness():
    codes = {generate_code() for _ in range(200)}
    assert len(codes) == 200, "Dois códigos idênticos em 200 tentativas — falha de aleatoriedade"


# ---------------------------------------------------------------------------
# generate_salt
# ---------------------------------------------------------------------------

def test_generate_salt_size():
    salt = generate_salt()
    assert isinstance(salt, bytes)
    assert len(salt) == SALT_SIZE


def test_generate_salt_uniqueness():
    salts = {generate_salt() for _ in range(100)}
    assert len(salts) == 100


# ---------------------------------------------------------------------------
# derive_key
# ---------------------------------------------------------------------------

def test_derive_key_size():
    key = derive_key(generate_code(), generate_salt())
    assert isinstance(key, bytes)
    assert len(key) == KEY_SIZE


def test_derive_key_deterministic():
    code = generate_code()
    salt = generate_salt()
    key1 = derive_key(code, salt)
    key2 = derive_key(code, salt)
    assert key1 == key2


def test_derive_key_different_salts_produce_different_keys():
    code = generate_code()
    key1 = derive_key(code, generate_salt())
    key2 = derive_key(code, generate_salt())
    assert key1 != key2


def test_derive_key_different_codes_produce_different_keys():
    salt = generate_salt()
    key1 = derive_key(generate_code(), salt)
    key2 = derive_key(generate_code(), salt)
    assert key1 != key2


def test_derive_key_rejects_empty_code():
    with pytest.raises(ValueError):
        derive_key("", generate_salt())


def test_derive_key_rejects_wrong_salt_size():
    with pytest.raises(ValueError):
        derive_key(generate_code(), b"tooshort")


# ---------------------------------------------------------------------------
# encrypt_body / decrypt_body
# ---------------------------------------------------------------------------

def test_encrypt_returns_base64_strings():
    key = secrets.token_bytes(KEY_SIZE)
    ct_b64, nonce_b64 = encrypt_body("teste", key)
    # Deve ser possível fazer decode sem erro
    base64.b64decode(ct_b64)
    base64.b64decode(nonce_b64)


def test_encrypt_nonce_size():
    key = secrets.token_bytes(KEY_SIZE)
    _, nonce_b64 = encrypt_body("teste", key)
    assert len(base64.b64decode(nonce_b64)) == NONCE_SIZE


def test_encrypt_produces_ciphertext_different_from_plaintext():
    key = secrets.token_bytes(KEY_SIZE)
    plaintext = "mensagem secreta"
    ct_b64, _ = encrypt_body(plaintext, key)
    assert ct_b64 != plaintext
    assert base64.b64decode(ct_b64) != plaintext.encode()


def test_encrypt_decrypt_roundtrip():
    key = secrets.token_bytes(KEY_SIZE)
    plaintext = "Olá, esta é uma mensagem secreta do projeto SI!"
    ct_b64, nonce_b64 = encrypt_body(plaintext, key)
    assert decrypt_body(ct_b64, key, nonce_b64) == plaintext


def test_encrypt_unique_nonces_each_call():
    key = secrets.token_bytes(KEY_SIZE)
    nonces = {encrypt_body("msg", key)[1] for _ in range(50)}
    assert len(nonces) == 50, "Nonce reutilizado — vulnerabilidade crítica em CTR"


def test_wrong_key_decrypt_produces_different_output():
    """Com chave errada, a decifragem produz lixo (bytes inválidos UTF-8)
    ou texto diferente do original. Em ambos os casos, o HMAC teria falhado
    antes de chegar aqui — este teste verifica apenas que a chave errada
    não recupera o plaintext."""
    key1 = secrets.token_bytes(KEY_SIZE)
    key2 = secrets.token_bytes(KEY_SIZE)
    plaintext = "mensagem original"
    ct_b64, nonce_b64 = encrypt_body(plaintext, key1)
    try:
        decrypted = decrypt_body(ct_b64, key2, nonce_b64)
        assert decrypted != plaintext
    except UnicodeDecodeError:
        pass  # bytes aleatórios não são UTF-8 válido — comportamento correto


def test_encrypt_rejects_wrong_key_size():
    with pytest.raises(ValueError):
        encrypt_body("msg", b"chave_curta")


def test_decrypt_rejects_wrong_key_size():
    key = secrets.token_bytes(KEY_SIZE)
    ct_b64, nonce_b64 = encrypt_body("msg", key)
    with pytest.raises(ValueError):
        decrypt_body(ct_b64, b"chave_curta", nonce_b64)


def test_encrypt_decrypt_empty_message():
    key = secrets.token_bytes(KEY_SIZE)
    ct_b64, nonce_b64 = encrypt_body("", key)
    assert decrypt_body(ct_b64, key, nonce_b64) == ""


def test_encrypt_decrypt_unicode_message():
    key = secrets.token_bytes(KEY_SIZE)
    plaintext = "Mensagem com acentos: ção, à, ê — e emojis: 🔐"
    ct_b64, nonce_b64 = encrypt_body(plaintext, key)
    assert decrypt_body(ct_b64, key, nonce_b64) == plaintext


# ---------------------------------------------------------------------------
# compute_hmac / verify_hmac
# ---------------------------------------------------------------------------

def test_hmac_verify_valid_mac():
    key = secrets.token_bytes(KEY_SIZE)
    ct_b64, _ = encrypt_body("mensagem", key)
    mac = compute_hmac(ct_b64, key)
    assert verify_hmac(ct_b64, key, mac)


def test_hmac_verify_tampered_ciphertext_fails():
    key = secrets.token_bytes(KEY_SIZE)
    ct_b64, _ = encrypt_body("mensagem", key)
    mac = compute_hmac(ct_b64, key)
    tampered = base64.b64encode(b"criptograma adulterado").decode()
    assert not verify_hmac(tampered, key, mac)


def test_hmac_verify_wrong_key_fails():
    key1 = secrets.token_bytes(KEY_SIZE)
    key2 = secrets.token_bytes(KEY_SIZE)
    ct_b64, _ = encrypt_body("mensagem", key1)
    mac = compute_hmac(ct_b64, key1)
    assert not verify_hmac(ct_b64, key2, mac)


def test_hmac_verify_truncated_mac_fails():
    key = secrets.token_bytes(KEY_SIZE)
    ct_b64, _ = encrypt_body("mensagem", key)
    mac = compute_hmac(ct_b64, key)
    truncated = mac[:10]
    assert not verify_hmac(ct_b64, key, truncated)


# ---------------------------------------------------------------------------
# Fluxo completo — simula o que as routes vão fazer
# ---------------------------------------------------------------------------

def test_full_encryption_flow():
    """
    Fluxo completo do Cenário 1 + Cenário 2 do enunciado:
      Emissor: code + salt + key → encrypt + hmac
      Destinatário: code + salt → mesma key → verify hmac → decrypt
    """
    plaintext = "Este é o corpo secreto do email que o destinatário vai ler."

    # --- lado do emissor ---
    code = generate_code()
    salt = generate_salt()
    key = derive_key(code, salt)
    ct_b64, nonce_b64 = encrypt_body(plaintext, key)
    mac = compute_hmac(ct_b64, key)

    # guardar na BD: code, salt, ct_b64, nonce_b64, mac
    # enviar por email: code, ct_b64

    # --- lado do destinatário (usa o code do email + salt da BD) ---
    recipient_key = derive_key(code, salt)  # mesma chave, derivada de novo

    assert verify_hmac(ct_b64, recipient_key, mac), "HMAC inválido — mensagem adulterada"
    result = decrypt_body(ct_b64, recipient_key, nonce_b64)
    assert result == plaintext


def test_full_flow_detects_tampered_message():
    """Garante que a decifragem falha silenciosamente quando o MAC é inválido."""
    plaintext = "mensagem original"
    code = generate_code()
    salt = generate_salt()
    key = derive_key(code, salt)
    ct_b64, _ = encrypt_body(plaintext, key)
    mac = compute_hmac(ct_b64, key)

    tampered_ct = base64.b64encode(b"adulterado").decode()
    assert not verify_hmac(tampered_ct, key, mac), "MAC devia falhar para criptograma adulterado"
