"""
Teste de cifragem/decifragem básico (skeleton atualizado).
Ver test_crypto.py para a suite de testes completa.
"""

from app.services.crypto import (
    decrypt_body,
    derive_key,
    encrypt_body,
    generate_code,
    generate_salt,
)


def test_cypher_and_decypher():
    msg = "Hello world"
    code = generate_code()
    salt = generate_salt()
    key = derive_key(code, salt)

    ciphertext_b64, nonce_b64 = encrypt_body(msg, key)

    assert ciphertext_b64 != msg
    assert decrypt_body(ciphertext_b64, key, nonce_b64) == msg
