from flask import request, jsonify, session
from app.routes import messages_bp
from app.models import Message, Receipt, User
from app.extensions import db
from app.services.crypto import generate_code, generate_salt, derive_key, encrypt_body, compute_hmac, decrypt_body, verify_hmac, PBKDF2_ITERATIONS
from app.services.auth import verify_login
from app.services.email import enviar_email_cifrado
import base64
from datetime import datetime, timezone

@messages_bp.route("/send", methods=["POST"])
def send_message():
    if "user_id" not in session:
        return jsonify({"error": "Não autenticado"}), 401
    
    data = request.get_json()
    if not data or not data.get("recipient_email") or not data.get("subject") or not data.get("body"):
        return jsonify({"error": "Parâmetros em falta"}), 400

    recipient_email = data["recipient_email"]
    subject = data["subject"]
    plain_text_body = data["body"]
    notification_email = (data.get("notification_email") or "").strip().lower() or None

    # Generates code and crypto materials
    code = generate_code()
    salt = generate_salt()
    
    key = derive_key(code, salt)
    
    encrypted_body_b64, iv_nonce_b64 = encrypt_body(plain_text_body, key)
    msg_hmac = compute_hmac(encrypted_body_b64, key)
    
    # Save the message
    sender_id = session["user_id"]
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

    # Save the pending receipt
    recipient_user = db.session.query(User).filter_by(user_id=recipient_email).first() # Just in case it's an internal user
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

    # Send the email
    enviar_email_cifrado(recipient_email, subject, code, encrypted_body_b64)

    return jsonify({"message": "Mensagem enviada com sucesso", "code": code}), 201

@messages_bp.route("/decrypt", methods=["POST"])
def decrypt_message():
    data = request.get_json()
    if not data or not data.get("code") or not data.get("password") or not data.get("encrypted_body"):
        return jsonify({"error": "Parâmetros em falta (código, password, ou corpo cifrado)"}), 400

    code = data["code"]
    provided_password = data["password"]
    provided_encrypted_body = data["encrypted_body"]

    message = db.session.query(Message).filter_by(code=code).first()

    if not message:
        return jsonify({"error": "Mensagem não encontrada"}), 404

    # Verify that the provided encrypted body matches the one in DB
    if message.encrypted_body != provided_encrypted_body:
        return jsonify({"error": "O corpo cifrado fornecido não corresponde à mensagem original."}), 400

    # --- Validate recipient identity using password ---
    receipt = db.session.query(Receipt).filter_by(message_id=message.id).first()
    if receipt and not receipt.confirmed_read:
        recipient_user = db.session.query(User).filter_by(user_id=receipt.recipient_email).first()
        if recipient_user:
            if not verify_login(receipt.recipient_email, provided_password):
                return jsonify({"error": "Password incorreta."}), 401

    # --- Decrypt the message body ---
    salt = base64.b64decode(message.code_salt)
    key = derive_key(code, salt, iterations=message.pbkdf2_iterations)

    if message.hmac:
        is_valid = verify_hmac(message.encrypted_body, key, message.hmac)
        if not is_valid:
            return jsonify({"error": "A integridade da mensagem foi comprometida (HMAC inválido)."}), 400

    decrypted_text = decrypt_body(message.encrypted_body, key, message.iv_nonce)

    # --- Generate receipt text for client-side signing ---
    receipt_text = None
    if receipt and not receipt.confirmed_read and receipt.recipient_user_id:
        receipt_text = f"Recibo de Leitura - Mensagem: {message.id} - Destinatário: {receipt.recipient_email} - Data: {datetime.now(timezone.utc).isoformat()}"
        receipt.receipt_text = receipt_text
        db.session.commit()
    elif receipt and not receipt.confirmed_read:
        receipt.confirmed_read = True
        db.session.commit()

    return jsonify({
        "subject": message.subject,
        "sender_id": message.sender_id,
        "body": decrypted_text,
        "receipt_text": receipt_text
    })
