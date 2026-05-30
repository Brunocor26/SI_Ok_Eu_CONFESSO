from app.extensions import db
from app.services.auth import register_user
from app.models import User, UserKey
import pytest

def test_register_creates_user_and_keys(app):
    """
    Testa se o serviço de registo cria efetivamente o utilizador, gera 
    o par de chaves RSA e encripta a chave privada na base de dados.
    """
    # Arrange (Não é preciso arranjo além da app inicializada)
    password = "minha_pass_super_segura_123456"
    username = "testuser"

    # Act
    user, public_pem, private_pem = register_user(username, password)

    # Assert - Verificar se o utilizador foi criado
    assert user.id is not None
    assert public_pem.startswith("-----BEGIN PUBLIC KEY-----")
    assert private_pem.startswith("-----BEGIN RSA PRIVATE KEY-----") or \
           private_pem.startswith("-----BEGIN PRIVATE KEY-----")
    
    # Query para garantir persistência na base de dados (SQLite em memória)
    saved_user = db.session.get(User, user.id)
    assert saved_user is not None
    assert saved_user.hash_algorithm == "pbkdf2_sha256"
    
    # Verificar se as chaves foram criadas na tabela auxiliar
    user_key = db.session.query(UserKey).filter_by(user_id=saved_user.id).first()
    assert user_key is not None
    assert user_key.public_key.startswith("-----BEGIN PUBLIC KEY-----")
    
    # Conferir integridade de parâmetros RSA originais
    assert user_key.rsa_key_size == 2048
