"""
Teste de integração — fluxo completo emissor → destinatário
============================================================
1. Registo de dois utilizadores (emissor e destinatário)
2. Emissor envia mensagem com email de notificação
3. Destinatário confirma receção (/receipts/verify)
4. Destinatário decifra → recebe receipt_text (/messages/decrypt)
5. Destinatário assina receipt_text localmente (Python, simula o browser)
6. Destinatário envia assinatura → /receipts/submit-signature
7. Verifica que o email de notificação foi enviado ao emissor
8. Emissor verifica recibo → lido, assinatura válida (/receipts/check)
"""

import base64
import hashlib
import pytest
from unittest.mock import patch

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding as asym_padding

from app.extensions import db
from app.models import Message, Receipt, User, UserKey
from app.services.crypto import (
    generate_code, generate_salt, derive_key, encrypt_body, compute_hmac,
    PBKDF2_ITERATIONS, hash_password, generate_rsa_key_pair,
)


def derive_user_id(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def sign_receipt(receipt_text: str, private_pem: str) -> str:
    """Assina o receipt_text com SHA256withRSA — idêntico ao que o browser faz."""
    private_key = serialization.load_pem_private_key(private_pem.encode("ascii"), password=None)
    sig = private_key.sign(receipt_text.encode("utf-8"), asym_padding.PKCS1v15(), hashes.SHA256())
    return base64.b64encode(sig).decode("ascii")


EMISSOR_PWD        = "password_emissor_16ch!"
DESTINATARIO_PWD   = "password_dest_16char!"
NOTIFICATION_EMAIL = "emissor@notificacao.pt"
PLAINTEXT          = "Esta é uma mensagem secreta de teste."


@pytest.fixture
def fluxo(app):
    with app.app_context():
        # --- Emissor ---
        pw_hash, pw_salt = hash_password(EMISSOR_PWD)
        emissor = User(
            user_id=derive_user_id(EMISSOR_PWD),
            password_hash=pw_hash,
            password_salt=pw_salt,
        )
        db.session.add(emissor)
        db.session.flush()

        # --- Destinatário: guardamos o PEM em bruto para assinar no teste ---
        pub_pem, priv_pem_raw = generate_rsa_key_pair()
        pw_hash2, pw_salt2 = hash_password(DESTINATARIO_PWD)
        destinatario = User(
            user_id=derive_user_id(DESTINATARIO_PWD),
            password_hash=pw_hash2,
            password_salt=pw_salt2,
        )
        db.session.add(destinatario)
        db.session.flush()
        db.session.add(UserKey(user_id=destinatario.id, public_key=pub_pem))

        # --- Mensagem cifrada ---
        code   = generate_code()
        salt   = generate_salt()
        key    = derive_key(code, salt)
        ct_b64, iv_b64 = encrypt_body(PLAINTEXT, key)
        mac    = compute_hmac(ct_b64, key)

        msg = Message(
            sender_id=emissor.id,
            recipient_email="destinatario@teste.pt",
            subject="Mensagem secreta",
            encrypted_body=ct_b64,
            code=code,
            code_salt=base64.b64encode(salt).decode("ascii"),
            pbkdf2_iterations=PBKDF2_ITERATIONS,
            cipher_algo="AES-256-CTR",
            iv_nonce=iv_b64,
            hmac=mac,
            sender_notification_email=NOTIFICATION_EMAIL,
        )
        db.session.add(msg)
        db.session.flush()

        receipt = Receipt(
            message_id=msg.id,
            recipient_email="destinatario@teste.pt",
            recipient_user_id=destinatario.id,
            confirmed_received=False,
            confirmed_read=False,
        )
        db.session.add(receipt)
        db.session.commit()

        yield {
            "code":          code,
            "encrypted_body": ct_b64,
            "priv_pem_raw":  priv_pem_raw,
            "message_id":    msg.id,
        }


def test_fluxo_completo(client, fluxo):
    code           = fluxo["code"]
    encrypted_body = fluxo["encrypted_body"]
    priv_pem_raw   = fluxo["priv_pem_raw"]

    # 1. Confirmar receção
    r = client.post("/api/receipts/verify", json={"code": code})
    assert r.status_code == 200, r.get_json()

    # 2. Decifrar mensagem
    r = client.post("/api/messages/decrypt", json={
        "code":           code,
        "password":       DESTINATARIO_PWD,
        "encrypted_body": encrypted_body,
    })
    assert r.status_code == 200, r.get_json()
    data = r.get_json()
    assert data["body"] == PLAINTEXT
    assert data["subject"] == "Mensagem secreta"
    receipt_text = data["receipt_text"]
    assert receipt_text is not None

    # 3. Assinar o recibo localmente (simula o browser)
    signature = sign_receipt(receipt_text, priv_pem_raw)

    # 4. Enviar assinatura → confirmar leitura + notificar emissor
    with patch("app.routes.receipts.enviar_notificacao_leitura") as mock_email:
        r = client.post("/api/receipts/submit-signature", json={
            "code":      code,
            "signature": signature,
        })
        assert r.status_code == 200, r.get_json()
        mock_email.assert_called_once_with(NOTIFICATION_EMAIL, receipt_text)

    # 5. Verificar recibo — leitura confirmada e assinatura válida
    r = client.post("/api/receipts/check", json={"code": code})
    assert r.status_code == 200, r.get_json()
    check = r.get_json()
    assert check["read"] is True
    assert check["confirmed_received"] is True
    assert check["signature_valid"] is True
    assert check["receipt_text"] == receipt_text
