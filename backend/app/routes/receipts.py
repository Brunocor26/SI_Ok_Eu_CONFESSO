from flask import request, jsonify
from app.routes import receipts_bp
from app.models import Message, Receipt, UserKey
from app.extensions import db
from app.services.crypto import verify_receipt_signature
from app.services.email import enviar_notificacao_leitura


@receipts_bp.route("/verify", methods=["POST"])
def verify_receipt():
    data = request.get_json()
    if not data or not data.get("code"):
        return jsonify({"error": "Código em falta"}), 400

    code = data["code"]
    message = db.session.query(Message).filter_by(code=code).first()

    if not message:
        return jsonify({"error": "Mensagem não encontrada"}), 404

    receipt = db.session.query(Receipt).filter_by(message_id=message.id).first()
    if receipt:
        receipt.confirmed_received = True
        db.session.commit()

    return jsonify({"message": "Receção confirmada com sucesso!"})


@receipts_bp.route("/confirm-read", methods=["POST"])
def confirm_read():
    data = request.get_json()
    if not data or not data.get("code") or not data.get("signature"):
        return jsonify({"error": "Código e assinatura são obrigatórios"}), 400

    code = data["code"]
    signature_b64 = data["signature"]

    message = db.session.query(Message).filter_by(code=code).first()
    if not message:
        return jsonify({"error": "Mensagem não encontrada"}), 404

    receipt = db.session.query(Receipt).filter_by(message_id=message.id).first()
    if not receipt or not receipt.receipt_text:
        return jsonify({"error": "Recibo não encontrado ou texto em falta"}), 404

    if receipt.confirmed_read:
        return jsonify({"message": "Recibo já confirmado"}), 200

    if not receipt.recipient_user_id:
        return jsonify({"error": "Destinatário sem conta registada"}), 400

    user_key = db.session.query(UserKey).filter_by(user_id=receipt.recipient_user_id).first()
    if not user_key:
        return jsonify({"error": "Chave pública do destinatário não encontrada"}), 404

    if not verify_receipt_signature(receipt.receipt_text, signature_b64, user_key.public_key):
        return jsonify({"error": "Assinatura inválida"}), 401

    receipt.confirmed_read = True
    receipt.signature = signature_b64
    db.session.commit()

    if message.sender_notification_email:
        enviar_notificacao_leitura(message.sender_notification_email, receipt.receipt_text)

    return jsonify({"message": "Leitura confirmada com sucesso"})


@receipts_bp.route("/check", methods=["POST"])
def check_receipt():
    data = request.get_json()
    if not data or not data.get("code"):
        return jsonify({"error": "Código em falta"}), 400

    code = data["code"]
    message = db.session.query(Message).filter_by(code=code).first()

    if not message:
        return jsonify({"error": "Mensagem não encontrada"}), 404

    receipt = db.session.query(Receipt).filter_by(message_id=message.id).first()

    if not receipt:
        return jsonify({
            "read": False,
            "confirmed_received": False,
            "signature_valid": False,
            "receipt_text": None,
        })

    signature_valid = False
    if receipt.confirmed_read and receipt.signature and receipt.receipt_text:
        if receipt.recipient_user_id:
            user_key = db.session.query(UserKey).filter_by(user_id=receipt.recipient_user_id).first()
            if user_key:
                try:
                    signature_valid = verify_receipt_signature(
                        receipt.receipt_text, receipt.signature, user_key.public_key
                    )
                except Exception:
                    signature_valid = False

    return jsonify({
        "read": receipt.confirmed_read,
        "confirmed_received": receipt.confirmed_received,
        "signature_valid": signature_valid,
        "receipt_text": receipt.receipt_text if receipt.confirmed_read else None,
    })
