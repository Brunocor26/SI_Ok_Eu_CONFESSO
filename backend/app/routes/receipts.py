from flask import request, jsonify
from app.routes import receipts_bp
from app.models import Message, Receipt
from app.extensions import db

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
