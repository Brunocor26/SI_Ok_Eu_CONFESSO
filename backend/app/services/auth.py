from app.extensions import db
from app.models import User, UserKey
from app.services.crypto import hash_password, generate_rsa_key_pair, encrypt_private_key

def register_user(password: str) -> User:
    """
    Registers a new user given a password.
    1. Hashes the password and saves the User.
    2. Generates an RSA key pair.
    3. Encrypts the private key with the user's password.
    4. Saves the UserKey.
    """
    if not password or len(password) < 16:
        raise ValueError("A password deve ter pelo menos 16 caracteres.")

    # 1. Hashing do password do utilizador
    password_hash, password_salt = hash_password(password)
    
    user = User(
        password_hash=password_hash,
        password_salt=password_salt
    )
    db.session.add(user)
    db.session.flush()  # Para obter o user.id gerado
    
    # 2. Geração do par de chaves RSA
    public_pem, private_pem = generate_rsa_key_pair()
    
    # 3. Encriptação da private key com a password em plain-text localmente (zero-knowledge)
    encrypted_priv, iv, priv_salt = encrypt_private_key(private_pem, password)
    
    # 4. Gravar chaves na BD
    user_key = UserKey(
        user_id=user.id,
        public_key=public_pem,
        encrypted_private_key=encrypted_priv,
        private_key_iv=iv,
        private_key_salt=priv_salt
    )
    db.session.add(user_key)
    db.session.commit()
    
    return user
