from flask import request, jsonify, session
from app.routes import messages_bp
from app.models import Message, Receipt, User
from app.extensions import db
from app.services.crypto import generate_code, generate_salt, derive_key, encrypt_body, compute_hmac, decrypt_body, verify_hmac, PBKDF2_ITERATIONS
from app.services.email import enviar_email_cifrado
import base64

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
        hmac=msg_hmac
    )
    
    db.session.add(new_message)
    db.session.flush() # get id

    # Save the pending receipt
    recipient_user = db.session.query(User).filter_by(username=recipient_email).first() # Just in case it's an internal user
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
    if not data or not data.get("code"):
        return jsonify({"error": "Código em falta"}), 400

    code = data["code"]
    message = db.session.query(Message).filter_by(code=code).first()
    
    if not message:
        return jsonify({"error": "Mensagem não encontrada"}), 404
        
    salt = base64.b64decode(message.code_salt)
    key = derive_key(code, salt, iterations=message.pbkdf2_iterations)
    
    if message.hmac:
        is_valid = verify_hmac(message.encrypted_body, key, message.hmac)
        if not is_valid:
            return jsonify({"error": "A integridade da mensagem foi comprometida (HMAC inválido)."}), 400
            
    decrypted_text = decrypt_body(message.encrypted_body, key, message.iv_nonce)
    
    # Mark as read
    receipt = db.session.query(Receipt).filter_by(message_id=message.id).first()
    if receipt:
        receipt.confirmed_read = True
        db.session.commit()
    
    return jsonify({
        "subject": message.subject,
        "sender_id": message.sender_id,
        "body": decrypted_text
    })
