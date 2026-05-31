"""
Testes relacionados com envio de email.

test_envio_email              — smoke test real via Mailpit (requer infraestrutura).
test_notificacao_leitura_*    — testes de integração com mock; não precisam de Mailpit.
"""

import base64
import hashlib
import smtplib
import time
import pytest
import requests
from unittest.mock import patch

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding as asym_padding

from app.extensions import db
from app.models import Message, Receipt, User, UserKey
from app.services.crypto import (
    generate_code, generate_salt, derive_key, encrypt_body, compute_hmac,
    PBKDF2_ITERATIONS, hash_password, generate_rsa_key_pair,
)
from app.services.email import enviar_email_cifrado

MAILPIT_HOST = 'localhost'
MAILPIT_PORT = 1025

SENDER_PWD        = "password_emissor_notif_16ch!"
RECIPIENT_PWD     = "password_dest_notif_16char!"
NOTIFICATION_EMAIL = "emissor_notif@teste.pt"
PLAINTEXT          = "Mensagem de teste para notificação."


def _mailpit_disponivel() -> bool:
    try:
        with smtplib.SMTP(MAILPIT_HOST, MAILPIT_PORT, timeout=2):
            return True
    except OSError:
        return False


def _uid(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def _sign(receipt_text: str, private_pem: str) -> str:
    key = serialization.load_pem_private_key(private_pem.encode("ascii"), password=None)
    sig = key.sign(receipt_text.encode("utf-8"), asym_padding.PKCS1v15(), hashes.SHA256())
    return base64.b64encode(sig).decode("ascii")


# ---------------------------------------------------------------------------
# Fixture partilhada: cria utilizadores, mensagem e recibo prontos para assinar
# ---------------------------------------------------------------------------

@pytest.fixture
def cenario_notificacao(app):
    """
    Prepara o estado mínimo para testar a notificação:
    - emissor com sender_notification_email definido
    - destinatário com par RSA
    - mensagem cifrada na BD
    - recibo com receipt_text já preenchido (passo decrypt já feito)
    """
    with app.app_context():
        # Emissor
        ph, ps = hash_password(SENDER_PWD)
        emissor = User(user_id=_uid(SENDER_PWD), password_hash=ph, password_salt=ps)
        db.session.add(emissor)
        db.session.flush()

        # Destinatário + chaves RSA
        pub_pem, priv_pem_raw = generate_rsa_key_pair()
        ph2, ps2 = hash_password(RECIPIENT_PWD)
        dest = User(user_id=_uid(RECIPIENT_PWD), password_hash=ph2, password_salt=ps2)
        db.session.add(dest)
        db.session.flush()
        db.session.add(UserKey(user_id=dest.id, public_key=pub_pem))

        # Mensagem cifrada com email de notificação
        code  = generate_code()
        salt  = generate_salt()
        key   = derive_key(code, salt)
        ct, iv = encrypt_body(PLAINTEXT, key)
        mac   = compute_hmac(ct, key)

        msg = Message(
            sender_id=emissor.id,
            recipient_email="dest@teste.pt",
            subject="Teste notificação",
            encrypted_body=ct,
            code=code,
            code_salt=base64.b64encode(salt).decode("ascii"),
            pbkdf2_iterations=PBKDF2_ITERATIONS,
            cipher_algo="AES-256-CTR",
            iv_nonce=iv,
            hmac=mac,
            sender_notification_email=NOTIFICATION_EMAIL,
        )
        db.session.add(msg)
        db.session.flush()

        # Recibo com receipt_text já gerado (simula que o decrypt já foi feito)
        receipt_text = f"Recibo de Leitura - Mensagem: {msg.id} - Destinatário: dest@teste.pt"
        receipt = Receipt(
            message_id=msg.id,
            recipient_email="dest@teste.pt",
            recipient_user_id=dest.id,
            confirmed_received=True,
            confirmed_read=False,
            receipt_text=receipt_text,
        )
        db.session.add(receipt)
        db.session.commit()

        yield {
            "code":         code,
            "priv_pem_raw": priv_pem_raw,
            "receipt_text": receipt_text,
        }


# ---------------------------------------------------------------------------
# Teste principal
# ---------------------------------------------------------------------------

def test_notificacao_enviada_ao_confirmar_leitura(client, cenario_notificacao):
    """Ao submeter a assinatura, o sistema deve enviar email de notificação ao emissor."""
    code         = cenario_notificacao["code"]
    receipt_text = cenario_notificacao["receipt_text"]
    signature    = _sign(receipt_text, cenario_notificacao["priv_pem_raw"])

    with patch("app.routes.receipts.enviar_notificacao_leitura") as mock_notif:
        r = client.post("/api/receipts/submit-signature", json={
            "code":      code,
            "signature": signature,
        })
        assert r.status_code == 200, r.get_json()
        mock_notif.assert_called_once_with(NOTIFICATION_EMAIL, receipt_text)


def test_notificacao_nao_enviada_sem_email_configurado(client, app):
    """Se o emissor não forneceu email de notificação, a função de envio não deve ser chamada."""
    with app.app_context():
        ph, ps = hash_password(SENDER_PWD + "2")
        emissor = User(user_id=_uid(SENDER_PWD + "2"), password_hash=ph, password_salt=ps)
        db.session.add(emissor)
        db.session.flush()

        pub_pem, priv_pem_raw = generate_rsa_key_pair()
        ph2, ps2 = hash_password(RECIPIENT_PWD + "2")
        dest = User(user_id=_uid(RECIPIENT_PWD + "2"), password_hash=ph2, password_salt=ps2)
        db.session.add(dest)
        db.session.flush()
        db.session.add(UserKey(user_id=dest.id, public_key=pub_pem))

        code = generate_code()
        salt = generate_salt()
        key  = derive_key(code, salt)
        ct, iv = encrypt_body("msg", key)
        mac  = compute_hmac(ct, key)

        msg = Message(
            sender_id=emissor.id,
            recipient_email="dest2@teste.pt",
            subject="Sem notif",
            encrypted_body=ct,
            code=code,
            code_salt=base64.b64encode(salt).decode("ascii"),
            pbkdf2_iterations=PBKDF2_ITERATIONS,
            cipher_algo="AES-256-CTR",
            iv_nonce=iv,
            hmac=mac,
            sender_notification_email=None,  # sem email de notificação
        )
        db.session.add(msg)
        db.session.flush()

        receipt_text = f"Recibo de Leitura - Mensagem: {msg.id} - Destinatário: dest2@teste.pt"
        receipt = Receipt(
            message_id=msg.id,
            recipient_email="dest2@teste.pt",
            recipient_user_id=dest.id,
            confirmed_received=True,
            confirmed_read=False,
            receipt_text=receipt_text,
        )
        db.session.add(receipt)
        db.session.commit()

        saved_code = code
        saved_priv = priv_pem_raw
        saved_text = receipt_text

    with patch("app.routes.receipts.enviar_notificacao_leitura") as mock_notif:
        signature = _sign(saved_text, saved_priv)
        r = client.post("/api/receipts/submit-signature", json={
            "code":      saved_code,
            "signature": signature,
        })
        assert r.status_code == 200, r.get_json()
        mock_notif.assert_not_called()


# ---------------------------------------------------------------------------
# Teste de integração real — sem mock, verifica o Mailpit directamente
# ---------------------------------------------------------------------------

MAILPIT_API = f"http://{MAILPIT_HOST}:8025/api/v1"


def _mailpit_limpar():
    """Apaga todas as mensagens do Mailpit antes do teste."""
    try:
        requests.delete(f"{MAILPIT_API}/messages", timeout=2)
    except Exception:
        pass


def _mailpit_mensagens() -> list:
    """Devolve a lista de mensagens actuais no Mailpit."""
    try:
        r = requests.get(f"{MAILPIT_API}/messages", timeout=2)
        return r.json().get("messages") or []
    except Exception:
        return []


@pytest.mark.skipif(
    not _mailpit_disponivel(),
    reason="Mailpit não está a correr (docker-compose up -d em ServicoEmail/)",
)
def test_notificacao_leitura_chega_ao_mailpit(client, cenario_notificacao):
    """
    Teste de integração real (sem mock):
    verifica que ao confirmar leitura, o email de notificação chega ao Mailpit.
    """
    _mailpit_limpar()

    code         = cenario_notificacao["code"]
    receipt_text = cenario_notificacao["receipt_text"]
    signature    = _sign(receipt_text, cenario_notificacao["priv_pem_raw"])

    r = client.post("/api/receipts/submit-signature", json={
        "code":      code,
        "signature": signature,
    })
    assert r.status_code == 200, r.get_json()

    # Pequena espera para o Mailpit processar
    time.sleep(0.3)

    mensagens = _mailpit_mensagens()
    destinatarios = [
        m["To"][0]["Address"]
        for m in mensagens
        if m.get("To")
    ]
    assert NOTIFICATION_EMAIL in destinatarios, (
        f"Email de notificação para '{NOTIFICATION_EMAIL}' não encontrado no Mailpit. "
        f"Mensagens presentes: {destinatarios}"
    )
    assuntos = [m["Subject"] for m in mensagens if m.get("To") and m["To"][0]["Address"] == NOTIFICATION_EMAIL]
    assert any("lida" in s.lower() for s in assuntos), (
        f"Assunto inesperado nos emails para '{NOTIFICATION_EMAIL}': {assuntos}"
    )


# ---------------------------------------------------------------------------
# Smoke test real (requer Mailpit activo)
# ---------------------------------------------------------------------------

@pytest.mark.skipif(
    not _mailpit_disponivel(),
    reason="Mailpit não está a correr (docker-compose up -d em ServicoEmail/)",
)
def test_envio_email():
    enviar_email_cifrado(
        destinatario='professor@universidade.pt',
        assunto='Mensagem Cifrada — OK-Eu-CONFESSO',
        codigo_acesso='A1B2C3D4E5F678901234567890ABCDEF',
        corpo_cifrado='U2FsdGVkX1+vxyz... (simulação do criptograma AES)',
        hmac_code='hmac-simulado-1234',
    )
