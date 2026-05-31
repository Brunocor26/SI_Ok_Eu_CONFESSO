import json
import pytest
from app.extensions import db
from app.services.auth import register_user
from app.models import User, UserKey


def test_register_creates_user_and_keys(app):
    """
    Verifica que o registo cria o utilizador, gera o par RSA e devolve a
    chave privada cifrada (JSON com metadados PBKDF2 + AES).
    """
    password = "minha_pass_super_segura_123456"
    user_id  = "testuserid"

    user, public_pem, encrypted_private = register_user(user_id, password)

    assert user.id is not None
    assert public_pem.startswith("-----BEGIN PUBLIC KEY-----")

    # A chave privada é devolvida cifrada como JSON (AES-256-CBC/CTR + PBKDF2)
    priv_meta = json.loads(encrypted_private)
    assert priv_meta["cipher"] in ("AES-256-CBC", "AES-256-CTR")
    assert "salt" in priv_meta
    assert "iv" in priv_meta
    assert "ciphertext" in priv_meta

    saved_user = db.session.get(User, user.id)
    assert saved_user is not None
    assert saved_user.hash_algorithm == "pbkdf2_sha256"

    user_key = db.session.query(UserKey).filter_by(user_id=saved_user.id).first()
    assert user_key is not None
    assert user_key.public_key.startswith("-----BEGIN PUBLIC KEY-----")
    assert user_key.rsa_key_size == 2048
