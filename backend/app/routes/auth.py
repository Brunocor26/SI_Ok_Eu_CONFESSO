from flask import request, jsonify, session
from app.routes import auth_bp
from app.services.auth import register_user, verify_login

@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    if not data or "username" not in data or "password" not in data:
        return jsonify({"error": "Parâmetros em falta"}), 400
        
    try:
        user = register_user(data["username"], data["password"])
        return jsonify({"message": "Registo efetuado com sucesso!", "user_id": user.id, "username": user.username}), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    if not data or "username" not in data or "password" not in data:
        return jsonify({"error": "Parâmetros em falta"}), 400
        
    user = verify_login(data["username"], data["password"])
    if user:
        session["user_id"] = user.id
        # Idealmente, o frontend só envia a password para o backend criar sessão 
        # Cuidado que na perspetiva de Zero-Knowledge The frontend precisará desta password 
        # para decifrar a private key mais tarde.
        return jsonify({"message": "Login com sucesso!", "username": user.username})
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
            return jsonify({"username": user.username, "id": user.id})
    return jsonify({"error": "Não autenticado"}), 401
