"""
Testes de integração para POST /messages/decrypt
=================================================
Testa o endpoint directamente, sem passar pelo frontend.
Cobre o fluxo feliz e todos os casos de rejeição.
"""

import base64
import pytest

from app.extensions import db
from app.models import Message, Receipt
from app.services.auth import register_user
from app.services.crypto import (
    generate_code, generate_salt, derive_key,
    encrypt_body, compute_hmac, PBKDF2_ITERATIONS,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

PASSWORD   = "password_segura_para_testes_16ch"
USERNAME   = "destinatario@teste.pt"
PLAINTEXT  = "Corpo secreto da mensagem de teste."


@pytest.fixture
def setup(app):
    """Regista utilizador e insere mensagem + recibo na BD."""
    with app.app_context():
        user, pub_pem, priv_pem = register_user(USERNAME, PASSWORD)

        code   = generate_code()
        salt   = generate_salt()
        key    = derive_key(code, salt)
        ct_b64, iv_b64 = encrypt_body(PLAINTEXT, key)
        mac    = compute_hmac(ct_b64, key)

        # Utilizador emissor (apenas para satisfazer a FK sender_id)
        from app.services.auth import register_user as ru
        sender, _, _ = ru("emissor@teste.pt", "password_emissor_segura_16ch")

        msg = Message(
            sender_id=sender.id,
            recipient_email=USERNAME,
            subject="Assunto de teste",
            encrypted_body=ct_b64,
            code=code,
            code_salt=base64.b64encode(salt).decode("ascii"),
            pbkdf2_iterations=PBKDF2_ITERATIONS,
            cipher_algo="AES-256-CTR",
            iv_nonce=iv_b64,
            hmac=mac,
        )
        db.session.add(msg)
        db.session.flush()

        receipt = Receipt(
            message_id=msg.id,
            recipient_email=USERNAME,
            recipient_user_id=user.id,
            confirmed_received=True,   # já confirmou receção
            confirmed_read=False,
        )
        db.session.add(receipt)
        db.session.commit()

        yield {
            "code":           code,
            "encrypted_body": ct_b64,
            "private_key":    priv_pem,
            "message_id":     msg.id,
        }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def post_decrypt(client, code, password, encrypted_body, private_key):
    return client.post(
        "/messages/decrypt",
        json={
            "code":           code,
            "password":       password,
            "encrypted_body": encrypted_body,
            "private_key":    private_key,
        },
    )


# ---------------------------------------------------------------------------
# Fluxo feliz
# ---------------------------------------------------------------------------

def test_decrypt_success(client, setup):
    """Fluxo completo: parâmetros correctos → mensagem decifrada + recibo assinado."""
    r = post_decrypt(
        client,
        setup["code"], PASSWORD, setup["encrypted_body"], setup["private_key"],
    )
    assert r.status_code == 200
    data = r.get_json()
    assert data["body"] == PLAINTEXT
    assert data["subject"] == "Assunto de teste"


def test_decrypt_marks_receipt_as_read(client, setup, app):
    """Após decifragem bem-sucedida, o recibo deve ficar com confirmed_read=True."""
    post_decrypt(
        client,
        setup["code"], PASSWORD, setup["encrypted_body"], setup["private_key"],
    )
    with app.app_context():
        receipt = db.session.query(Receipt).filter_by(
            message_id=setup["message_id"]
        ).first()
        assert receipt.confirmed_read is True
        assert receipt.signature is not None
        assert receipt.receipt_text is not None


def test_decrypt_twice_still_returns_body(client, setup):
    """Mensagem já lida pode ser decifrada novamente (recibo não é sobrescrito)."""
    post_decrypt(
        client,
        setup["code"], PASSWORD, setup["encrypted_body"], setup["private_key"],
    )
    r = post_decrypt(
        client,
        setup["code"], PASSWORD, setup["encrypted_body"], setup["private_key"],
    )
    assert r.status_code == 200
    assert r.get_json()["body"] == PLAINTEXT


# ---------------------------------------------------------------------------
# Parâmetros em falta
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("missing_field", ["code", "password", "encrypted_body", "private_key"])
def test_decrypt_missing_field_returns_400(client, setup, missing_field):
    payload = {
        "code":           setup["code"],
        "password":       PASSWORD,
        "encrypted_body": setup["encrypted_body"],
        "private_key":    setup["private_key"],
    }
    del payload[missing_field]
    r = client.post("/messages/decrypt", json=payload)
    assert r.status_code == 400


# ---------------------------------------------------------------------------
# Código inválido
# ---------------------------------------------------------------------------

def test_decrypt_wrong_code_returns_404(client, setup):
    r = post_decrypt(
        client,
        "codigoinexistente00000000000000", PASSWORD,
        setup["encrypted_body"], setup["private_key"],
    )
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# Corpo cifrado adulterado
# ---------------------------------------------------------------------------

def test_decrypt_tampered_body_returns_400(client, setup):
    """Corpo cifrado diferente do guardado na BD → rejeição imediata."""
    tampered = base64.b64encode(b"corpo adulterado pelo atacante").decode()
    r = post_decrypt(
        client,
        setup["code"], PASSWORD, tampered, setup["private_key"],
    )
    assert r.status_code == 400


# ---------------------------------------------------------------------------
# Password errada
# ---------------------------------------------------------------------------

def test_decrypt_wrong_password_returns_401(client, setup):
    r = post_decrypt(
        client,
        setup["code"], "password_errada_123456789012345",
        setup["encrypted_body"], setup["private_key"],
    )
    assert r.status_code == 401


# ---------------------------------------------------------------------------
# Chave privada errada (de outro utilizador)
# ---------------------------------------------------------------------------

def test_decrypt_wrong_private_key_returns_401(client, setup, app):
    """Chave privada que não corresponde à pública registada → rejeição."""
    with app.app_context():
        from app.services.crypto import generate_rsa_key_pair
        _, other_priv = generate_rsa_key_pair()

    r = post_decrypt(
        client,
        setup["code"], PASSWORD, setup["encrypted_body"], other_priv,
    )
    assert r.status_code == 401


def test_decrypt_invalid_pem_returns_400(client, setup):
    """PEM malformado → rejeição com 400."""
    r = post_decrypt(
        client,
        setup["code"], PASSWORD, setup["encrypted_body"],
        "isto nao e um pem valido",
    )
    assert r.status_code == 400


# ---------------------------------------------------------------------------
# Sem conta registada
# ---------------------------------------------------------------------------

def test_decrypt_unregistered_recipient_returns_403(client, app):
    """Destinatário sem conta → 403 antes de qualquer decifragem."""
    with app.app_context():
        from app.services.auth import register_user as ru
        from app.services.crypto import generate_rsa_key_pair
        sender, _, _ = ru("emissor2@teste.pt", "password_emissor2_segura_16ch")

        code   = generate_code()
        salt   = generate_salt()
        key    = derive_key(code, salt)
        ct_b64, iv_b64 = encrypt_body("msg", key)
        mac    = compute_hmac(ct_b64, key)
        _, priv = generate_rsa_key_pair()

        msg = Message(
            sender_id=sender.id,
            recipient_email="naoexiste@teste.pt",
            subject="Sem conta",
            encrypted_body=ct_b64,
            code=code,
            code_salt=base64.b64encode(salt).decode("ascii"),
            pbkdf2_iterations=PBKDF2_ITERATIONS,
            cipher_algo="AES-256-CTR",
            iv_nonce=iv_b64,
            hmac=mac,
        )
        db.session.add(msg)
        db.session.flush()

        receipt = Receipt(
            message_id=msg.id,
            recipient_email="naoexiste@teste.pt",
            recipient_user_id=None,
            confirmed_received=True,
            confirmed_read=False,
        )
        db.session.add(receipt)
        db.session.commit()
        saved_code   = code
        saved_ct     = ct_b64
        saved_priv   = priv

    r = post_decrypt(client, saved_code, PASSWORD, saved_ct, saved_priv)
    assert r.status_code == 403
