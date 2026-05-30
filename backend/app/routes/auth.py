from flask import request, jsonify
from app.routes import auth_bp
from app.services.auth import register_user
import secrets
import hashlib

_CHARS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$'

@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    key_cipher_algo = data.get("key_cipher_algo", "AES-256-CBC")
    try:
        rsa_key_size = int(data.get("rsa_key_size", 2048))
    except (ValueError, TypeError):
        return jsonify({"error": "Tamanho de chave RSA inválido"}), 400

    if key_cipher_algo not in ("AES-256-CBC", "AES-256-CTR"):
        return jsonify({"error": "Algoritmo de cifra de chave privada não suportado"}), 400
    if rsa_key_size not in (2048, 3072, 4096):
        return jsonify({"error": "Tamanho de chave RSA não suportado"}), 400

    password = ''.join(secrets.choice(_CHARS) for _ in range(16))
    identifier = hashlib.sha256(password.encode('utf-8')).hexdigest()

    try:
        user, public_key, private_key = register_user(
            identifier, password, key_cipher_algo=key_cipher_algo, rsa_key_size=rsa_key_size
        )
        #MANDA para o user (password, public_key, private_key)n
        return jsonify({
            "message": "Registo efetuado com sucesso!",
            "password": password,
            "public_key": public_key,
            "private_key": private_key,
        }), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

