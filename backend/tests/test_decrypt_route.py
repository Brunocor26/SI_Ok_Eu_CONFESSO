"""
Testes de integração para POST /messages/decrypt
=================================================
Nota: a chave privada é usada apenas no browser (Web Crypto API).
O endpoint /messages/decrypt não recebe nem valida chave privada —
a assinatura do recibo acontece depois, em /receipts/submit-signature.
"""

import base64
import hashlib
import pytest

from app.extensions import db
from app.models import Message, Receipt
from app.services.auth import register_user
from app.services.crypto import (
    generate_code, generate_salt, derive_key,
    encrypt_body, compute_hmac, PBKDF2_ITERATIONS,
)


PASSWORD  = "password_segura_para_testes_16ch"
PLAINTEXT = "Corpo secreto da mensagem de teste."


def _uid(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


@pytest.fixture
def setup(app):
    """Regista utilizador e insere mensagem + recibo na BD."""
    with app.app_context():
        # O user_id é o sha256 da password — igual ao que o endpoint faz
        user, _, _ = register_user(_uid(PASSWORD), PASSWORD)

        code   = generate_code()
        salt   = generate_salt()
        key    = derive_key(code, salt)
        ct_b64, iv_b64 = encrypt_body(PLAINTEXT, key)
        mac    = compute_hmac(ct_b64, key)

        sender, _, _ = register_user(_uid("password_emissor_segura_16ch"), "password_emissor_segura_16ch")

        msg = Message(
            sender_id=sender.id,
            recipient_email="destinatario@teste.pt",
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
            recipient_email="destinatario@teste.pt",
            recipient_user_id=user.id,
            confirmed_received=True,
            confirmed_read=False,
        )
        db.session.add(receipt)
        db.session.commit()

        yield {
            "code":           code,
            "encrypted_body": ct_b64,
            "message_id":     msg.id,
        }


def post_decrypt(client, code, password, encrypted_body):
    return client.post(
        "/api/messages/decrypt",
        json={"code": code, "password": password, "encrypted_body": encrypted_body},
    )


# ---------------------------------------------------------------------------
# Fluxo feliz
# ---------------------------------------------------------------------------

def test_decrypt_success(client, setup):
    r = post_decrypt(client, setup["code"], PASSWORD, setup["encrypted_body"])
    assert r.status_code == 200
    data = r.get_json()
    assert data["body"] == PLAINTEXT
    assert data["subject"] == "Assunto de teste"


def test_decrypt_sets_receipt_text(client, setup, app):
    """Após decifragem, receipt_text é gerado mas confirmed_read mantém-se False.
    A confirmação de leitura só ocorre após /receipts/submit-signature."""
    post_decrypt(client, setup["code"], PASSWORD, setup["encrypted_body"])
    with app.app_context():
        receipt = db.session.query(Receipt).filter_by(message_id=setup["message_id"]).first()
        assert receipt.receipt_text is not None
        assert receipt.confirmed_read is False


def test_decrypt_twice_still_returns_body(client, setup):
    """Mensagem já decifrada pode ser decifrada novamente."""
    post_decrypt(client, setup["code"], PASSWORD, setup["encrypted_body"])
    r = post_decrypt(client, setup["code"], PASSWORD, setup["encrypted_body"])
    assert r.status_code == 200
    assert r.get_json()["body"] == PLAINTEXT


# ---------------------------------------------------------------------------
# Parâmetros em falta
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("missing_field", ["code", "password", "encrypted_body"])
def test_decrypt_missing_field_returns_400(client, setup, missing_field):
    payload = {
        "code":           setup["code"],
        "password":       PASSWORD,
        "encrypted_body": setup["encrypted_body"],
    }
    del payload[missing_field]
    r = client.post("/api/messages/decrypt", json=payload)
    assert r.status_code == 400


# ---------------------------------------------------------------------------
# Código inválido
# ---------------------------------------------------------------------------

def test_decrypt_wrong_code_returns_404(client, setup):
    r = post_decrypt(client, "codigoinexistente00000000000000", PASSWORD, setup["encrypted_body"])
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# Corpo cifrado adulterado
# ---------------------------------------------------------------------------

def test_decrypt_tampered_body_returns_400(client, setup):
    tampered = base64.b64encode(b"corpo adulterado pelo atacante").decode()
    r = post_decrypt(client, setup["code"], PASSWORD, tampered)
    assert r.status_code == 400


# ---------------------------------------------------------------------------
# Password errada
# ---------------------------------------------------------------------------

def test_decrypt_wrong_password_returns_403(client, setup):
    # Neste sistema, o user_id é sha256(password), por isso uma password errada
    # resulta em "utilizador não encontrado" (403) e não "password incorreta" (401).
    r = post_decrypt(client, setup["code"], "password_errada_123456789012345", setup["encrypted_body"])
    assert r.status_code == 403


# ---------------------------------------------------------------------------
# Destinatário sem conta registada
# ---------------------------------------------------------------------------

def test_decrypt_unregistered_recipient_returns_403(client, app):
    with app.app_context():
        sender, _, _ = register_user(_uid("password_emissor2_segura_16ch"), "password_emissor2_segura_16ch")

        code   = generate_code()
        salt   = generate_salt()
        key    = derive_key(code, salt)
        ct_b64, iv_b64 = encrypt_body("msg", key)
        mac    = compute_hmac(ct_b64, key)

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
        saved_code = code
        saved_ct   = ct_b64

    r = post_decrypt(client, saved_code, PASSWORD, saved_ct)
    assert r.status_code == 403


# ---------------------------------------------------------------------------
# HMAC adulterado fornecido pelo destinatário
# ---------------------------------------------------------------------------

def test_decrypt_tampered_hmac_provided_returns_400(client, setup):
    r = client.post(
        "/api/messages/decrypt",
        json={
            "code":           setup["code"],
            "password":       PASSWORD,
            "encrypted_body": setup["encrypted_body"],
            "hmac":           "isto_nao_e_um_hmac_valido_1234567890",
        },
    )
    assert r.status_code == 400
