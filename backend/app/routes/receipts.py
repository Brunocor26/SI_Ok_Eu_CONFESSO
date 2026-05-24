from flask import request, jsonify
from app.routes import receipts_bp
from app.models import Message, Receipt, UserKey
from app.extensions import db
from app.services.crypto import verify_receipt_signature


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
