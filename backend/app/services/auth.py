from app.extensions import db
from app.models import User, UserKey
from app.services.crypto import hash_password, derive_key, PBKDF2_ITERATIONS, generate_rsa_key_pair
import base64
import hmac

def verify_login(user_id: str, password: str) -> User | None:
    """
    Verifica as credenciais de um utilizador.
    """
    user = db.session.query(User).filter_by(user_id=user_id).first()
    if not user:
        return None
        
    salt = base64.b64decode(user.password_salt)
    derived_key = derive_key(password, salt)
    derived_hash = base64.b64encode(derived_key).decode("ascii")
    
    if hmac.compare_digest(user.password_hash, derived_hash):
        return user
    return None

def register_user(user_id: str, password: str, key_cipher_algo: str = "AES-256-CBC", rsa_key_size: int = 2048) -> tuple[User, str, str]:
    """
    Registers a new user given a user_id and password.
    1. Hashes the password and saves the User.
    2. Generates an RSA key pair (with configurable size).
    3. Encrypts the private key with the user's password (with configurable cipher).
    4. Saves the UserKey.
    """
    if not user_id or not user_id.strip():
        raise ValueError("O nome de utilizador não pode ser vazio.")
    if not password or len(password) < 16:
        raise ValueError("A password deve ter pelo menos 16 caracteres.")
        
    # Verificar se utilizador já existe
    if db.session.query(User).filter_by(user_id=user_id).first():
        raise ValueError("Nome de utilizador já em uso.")
    # 1. Hashing do password do utilizador
    password_hash, password_salt = hash_password(password)

    user = User(
        user_id=user_id,
        password_hash=password_hash,
        password_salt=password_salt
    )
    db.session.add(user)
    db.session.flush()  # Para obter o user.id gerado
    
    # 2. Geração do par de chaves RSA
    public_pem, private_pem = generate_rsa_key_pair(key_size=rsa_key_size)
    
    # 3. Gravar apenas a chave pública na BD (a privada NUNCA é armazenada)
    user_key = UserKey(
        user_id=user.id,
        public_key=public_pem,
        rsa_key_size=rsa_key_size
    )
    db.session.add(user_key)
    db.session.commit()

    return user, public_pem, private_pem
