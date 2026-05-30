from flask import request, jsonify, session
from app.routes import auth_bp
from app.services.auth import register_user, verify_login
import secrets
import hashlib

_CHARS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$'

@auth_bp.route("/register", methods=["POST"])
def register():
    password = ''.join(secrets.choice(_CHARS) for _ in range(16))
    identifier = hashlib.sha256(password.encode('utf-8')).hexdigest()

    try:
        user, public_key, private_key = register_user(identifier, password)
        #MANDA para o user (password, public_key, private_key)n
        return jsonify({
            "message": "Registo efetuado com sucesso!",
            "password": password,
            "public_key": public_key,
            "private_key": private_key,
        }), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@auth_bp.route("/login", methods=["POST"])  #TODO: pq???
def login():
    data = request.get_json()
    if not data or "user_id" not in data or "password" not in data:
        return jsonify({"error": "Parâmetros em falta"}), 400

    user = verify_login(data["user_id"], data["password"])
    if user:
        session["user_id"] = user.id
        return jsonify({"message": "Login com sucesso!", "user_id": user.user_id})
    return jsonify({"error": "Credenciais inválidas"}), 401

@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.pop("user_id", None)
    return jsonify({"message": "Logout efetuado com sucesso"})

@auth_bp.route("/me", methods=["GET"])
def me():
    if "user_id" in session:
        from app.models import User
        from app.extensions import db
        user = db.session.get(User, session["user_id"])
        if user:
            return jsonify({"user_id": user.user_id, "id": user.id})
    return jsonify({"error": "Não autenticado"}), 401
