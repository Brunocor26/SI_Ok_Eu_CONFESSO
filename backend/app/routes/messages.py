from flask import request, jsonify, session
from app.routes import messages_bp
from app.models import Message, Receipt, User
from app.extensions import db
from app.services.crypto import generate_code, generate_salt, derive_key, encrypt_body, compute_hmac, decrypt_body, verify_hmac, PBKDF2_ITERATIONS
from app.services.auth import verify_login
from app.services.email import enviar_email_cifrado, enviar_notificacao_leitura
import base64
from datetime import datetime, timezone

@messages_bp.route("/send", methods=["POST"])
def send_message():
    data = request.get_json()
    if not data or not data.get("recipient_email") or not data.get("subject") or not data.get("body") or not data.get("password"):
        return jsonify({"error": "Parâmetros em falta (destinatário, assunto, corpo ou password)"}), 400

    recipient_email = data["recipient_email"]
    subject = data["subject"]
    plain_text_body = data["body"]
    provided_password = data["password"]
    notification_email = (data.get("notification_email") or "").strip().lower() or None

    # --- Validar a password do remetente e autenticar ---
    import hashlib
    pwd_hash = hashlib.sha256(provided_password.encode("utf-8")).hexdigest()
    sender_user = db.session.query(User).filter_by(user_id=pwd_hash).first()
    if not sender_user:
        return jsonify({"error": "Remetente não encontrado ou password incorreta."}), 401

    if not verify_login(sender_user.user_id, provided_password):
        return jsonify({"error": "Password incorreta."}), 401

    sender_id = sender_user.id

    # Gera o código e os materiais criptográficos
    code = generate_code()
    salt = generate_salt()
    
    key = derive_key(code, salt)
    
    encrypted_body_b64, iv_nonce_b64 = encrypt_body(plain_text_body, key)
    msg_hmac = compute_hmac(encrypted_body_b64, key)
    
    # Guardar a mensagem
    new_message = Message(
        sender_id=sender_id,
        recipient_email=recipient_email,
        subject=subject,
        encrypted_body=encrypted_body_b64,
        code=code,
        code_salt=base64.b64encode(salt).decode("ascii"),
        pbkdf2_iterations=PBKDF2_ITERATIONS,
        cipher_algo="AES-256-CTR",
        iv_nonce=iv_nonce_b64,
        hmac=msg_hmac,
        sender_notification_email=notification_email
    )
    
    db.session.add(new_message)
    db.session.flush() # get id

    # Guardar o recibo pendente
    recipient_user = db.session.query(User).filter_by(user_id=recipient_email).first() # Por precaução, caso seja um utilizador interno
    recipient_user_id = recipient_user.id if recipient_user else None

    new_receipt = Receipt(
        message_id=new_message.id,
        recipient_email=recipient_email,
        recipient_user_id=recipient_user_id,
        confirmed_received=False,
        confirmed_read=False
    )
    db.session.add(new_receipt)
    db.session.commit()

    # Enviar o email
    enviar_email_cifrado(recipient_email, subject, code, encrypted_body_b64, msg_hmac)

    return jsonify({"message": "Mensagem enviada com sucesso", "code": code}), 201

@messages_bp.route("/decrypt", methods=["POST"])
def decrypt_message():
    data = request.get_json()
    if not data or not data.get("code") or not data.get("password") or not data.get("encrypted_body"):
        return jsonify({"error": "Parâmetros em falta (código, password ou corpo cifrado)"}), 400

    code = data["code"]
    provided_password = data["password"]
    provided_encrypted_body = data["encrypted_body"]

    message = db.session.query(Message).filter_by(code=code).first()

    if not message:
        return jsonify({"error": "Mensagem não encontrada"}), 404

    # Verificar se o corpo cifrado fornecido corresponde ao que está na BD
    if message.encrypted_body != provided_encrypted_body:
        return jsonify({"error": "O corpo cifrado fornecido não corresponde à mensagem original."}), 400

    # --- Validar existência do recibo ---
    receipt = db.session.query(Receipt).filter_by(message_id=message.id).first()
    if not receipt:
        return jsonify({"error": "Recibo não encontrado"}), 404

    # --- Identificar o destinatário pela password fornecida ---
    import hashlib
    pwd_hash = hashlib.sha256(provided_password.encode("utf-8")).hexdigest()
    recipient_user = db.session.query(User).filter_by(user_id=pwd_hash).first()

    if not recipient_user:
        return jsonify({"error": "Destinatário sem conta registada"}), 403

    if not verify_login(recipient_user.user_id, provided_password):
        return jsonify({"error": "Password incorreta."}), 401

    # --- Verificar se o utilizador identificado corresponde ao recibo (se já estiver associado) ---
    if receipt.recipient_user_id and receipt.recipient_user_id != recipient_user.id:
        return jsonify({"error": "Esta mensagem foi enviada para outro destinatário."}), 403

    # --- Associar o recibo ao destinatário, se ainda não estiver ---
    if not receipt.recipient_user_id:
        receipt.recipient_user_id = recipient_user.id
        db.session.commit()

    # A validação da chave privada já não é feita aqui, pois o backend nunca
    # deve ter acesso à chave privada. A assinatura do recibo ocorre localmente
    # no browser e é enviada para o endpoint /receipts/submit-signature.

    # --- Opcional: Se o HMAC-SHA256 foi fornecido no payload, verificar! ---
    salt = base64.b64decode(message.code_salt)
    key = derive_key(code, salt, iterations=message.pbkdf2_iterations)

    if message.hmac:
        is_valid = verify_hmac(message.encrypted_body, key, message.hmac)
        if not is_valid:
            return jsonify({"error": "A integridade da mensagem foi comprometida (HMAC inválido)."}), 400

        provided_hmac = data.get("hmac")
        if provided_hmac and provided_hmac != message.hmac:
            return jsonify({"error": "O HMAC fornecido é inválido."}), 400

    # --- Decifrar o corpo da mensagem ---
    decrypted_text = decrypt_body(message.encrypted_body, key, message.iv_nonce)

    # --- Gera o texto do recibo para o frontend assinar ---
    if not receipt.confirmed_read:
        receipt_text = f"Recibo de Leitura - Mensagem: {message.id} - Destinatário: {receipt.recipient_email} - Data: {datetime.now(timezone.utc).isoformat()}"
        
        receipt.receipt_text = receipt_text
        # Não guardamos a assinatura aqui, nem marcamos como confirmed_read.
        # Isso só acontece quando o frontend envia a assinatura para /submit-signature
        db.session.commit()

    return jsonify({
        "subject": message.subject,
        "body": decrypted_text,
        "receipt_text": receipt.receipt_text
    })
