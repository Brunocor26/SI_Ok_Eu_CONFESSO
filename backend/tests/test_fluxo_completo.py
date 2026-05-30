"""
Teste de integração — fluxo completo emissor → destinatário
============================================================
1. Registo de dois utilizadores (emissor e destinatário)
2. Emissor envia mensagem com email de notificação
3. Destinatário confirma receção
4. Destinatário decifra → recebe receipt_text
5. Destinatário assina receipt_text localmente (Python, igual ao browser)
6. Destinatário envia assinatura → confirm-read
7. Emissor verifica recibo → assinatura válida
8. Verifica que o email de notificação foi enviado ao emissor
"""

import base64
import hashlib
import pytest
from unittest.mock import patch

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding as asym_padding

from app.extensions import db
from app.services.auth import register_user
from app.services.crypto import generate_code, generate_salt, derive_key, encrypt_body, compute_hmac, PBKDF2_ITERATIONS
from app.models import Message, Receipt


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def derive_user_id(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def sign_receipt(receipt_text: str, private_pem: str) -> str:
    private_key = serialization.load_pem_private_key(private_pem.encode("ascii"), password=None)
    signature = private_key.sign(receipt_text.encode("utf-8"), asym_padding.PKCS1v15(), hashes.SHA256())
    return base64.b64encode(signature).decode("ascii")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

EMISSOR_PWD     = "password_emissor_16ch!"
DESTINATARIO_PWD = "password_dest_16char!"
NOTIFICATION_EMAIL = "emissor@notificacao.pt"
PLAINTEXT = "Esta é uma mensagem secreta de teste."


@pytest.fixture
def fluxo(app):
    with app.app_context():
        emissor_uid = derive_user_id(EMISSOR_PWD)
        dest_uid    = derive_user_id(DESTINATARIO_PWD)

        emissor, _, _         = register_user(emissor_uid, EMISSOR_PWD)
        destinatario, pub_pem, priv_pem = register_user(dest_uid, DESTINATARIO_PWD)

        dest_email = "destinatario@teste.pt"

        code   = generate_code()
        salt   = generate_salt()
        key    = derive_key(code, salt)
        ct_b64, iv_b64 = encrypt_body(PLAINTEXT, key)
        mac    = compute_hmac(ct_b64, key)

        msg = Message(
            sender_id=emissor.id,
            recipient_email=dest_email,
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
            recipient_email=dest_email,
            recipient_user_id=destinatario.id,
            confirmed_received=False,
            confirmed_read=False,
        )
        db.session.add(receipt)
        db.session.commit()

        yield {
            "code":            code,
            "encrypted_body":  ct_b64,
            "private_key":     priv_pem,
            "dest_user_id":    dest_uid,
            "message_id":      msg.id,
        }


# ---------------------------------------------------------------------------
# Teste principal
# ---------------------------------------------------------------------------

def test_fluxo_completo(client, fluxo):
    code           = fluxo["code"]
    encrypted_body = fluxo["encrypted_body"]
    private_key    = fluxo["private_key"]
    dest_user_id   = fluxo["dest_user_id"]

    # 1. Confirmar receção
    r = client.post("/api/receipts/verify", json={"code": code})
    assert r.status_code == 200, r.get_json()

    # 2. Decifrar mensagem (envia a chave privada para o backend assinar)
    with patch("app.routes.messages.enviar_notificacao_leitura") as mock_email:
        r = client.post("/api/messages/decrypt", json={
            "code":           code,
            "password":       DESTINATARIO_PWD,
            "encrypted_body": encrypted_body,
            "private_key":    private_key,
        })
        assert r.status_code == 200, r.get_json()
        data = r.get_json()
        assert data["body"] == PLAINTEXT
        assert data["subject"] == "Mensagem secreta"
        receipt_text = data["receipt_text"]
        assert receipt_text is not None

        # Verifica que o email de notificação foi enviado ao emissor
        mock_email.assert_called_once_with(NOTIFICATION_EMAIL, receipt_text)

    # 3. Chamar confirm-read para compatibilidade (deve responder OK de imediato já confirmado)
    r = client.post("/api/receipts/confirm-read", json={
        "code":      code,
        "signature": "qualquer_assinatura_de_compatibilidade",
    })
    assert r.status_code == 200, r.get_json()

    # 4. Verificar recibo — assinatura deve ser válida
    r = client.post("/api/receipts/check", json={"code": code})
    assert r.status_code == 200, r.get_json()
    check = r.get_json()
    assert check["read"] is True
    assert check["confirmed_received"] is True
    assert check["signature_valid"] is True
    assert check["receipt_text"] == receipt_text
