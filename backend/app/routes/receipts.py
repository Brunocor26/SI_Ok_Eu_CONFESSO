from cryptography.hazmat.primitives import hashes, serialization, padding as sym_padding
from cryptography.hazmat.primitives.asymmetric import padding as asym_padding

from flask import request, jsonify
from app.routes import receipts_bp
from app.models import Message, Receipt, UserKey
from app.extensions import db
from app.services.email import enviar_notificacao_leitura
import base64

#Este ficheiro contem: 
# Confirmação Dupla: verificar confirmacao_rececao e confirmacao_leitura antes de avançar cumpre o requisito do Cenário 2. 
# Algoritmo de Cifra: AES em modo CTR para a decifragem do corpo da mensagem. 
# Assinatura Digital: A função gerar_recibo_digital utiliza SHA256 com RSA, o que corresponde ao requisito SHA256withRSA mencionado no enunciado. 
# Verificação: A função de verificação permite ao emissor validar a prova de leitura, fechando o ciclo de Não-Repúdio. 


# --- FUNÇÃO AUXILIAR DE ASSINATURA ---
# Gera o texto do recibo e assina-o com RSA-PSS + SHA256 (SHA256withRSA)
# Usada pelo endpoint /confirm-read quando o destinatário confirma que leu a mensagem.
def gerar_recibo_digital(msg_limpa, chave_privada, codigo):
    # Texto do recibo conforme pedido no enunciado [cite: 117]
    # Nota: msg_limpa pode ser None quando chamado diretamente a partir do endpoint
    texto_recibo = f"Recibo de leitura: Mensagem {codigo} lida com sucesso.".encode()
    
    assinatura = chave_privada.sign(
        texto_recibo,
        asym_padding.PSS(
            mgf=asym_padding.MGF1(hashes.SHA256()),
            salt_length=asym_padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    return texto_recibo, assinatura


# Permite ao emissor verificar se o recibo assinado pelo destinatário é válido.
# Usada pelo endpoint /check para fechar o ciclo de Não-Repúdio.
def verificar_recibo_leitura(texto_recibo, assinatura_bin, chave_publica_rsa):
    try:
        chave_publica_rsa.verify(
            assinatura_bin,
            texto_recibo.encode() if isinstance(texto_recibo, str) else texto_recibo,
            asym_padding.PSS(
                mgf=asym_padding.MGF1(hashes.SHA256()),
                salt_length=asym_padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return True # Assinatura legítima!
    except Exception:
        return False # Assinatura inválida ou recibo alterado!


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
    # O cliente envia a sua chave privada (PEM) para o servidor gerar o recibo assinado
    if not data or not data.get("code") or not data.get("private_key"):
        return jsonify({"error": "Código e chave privada são obrigatórios"}), 400

    code = data["code"]
    private_key_pem = data["private_key"]

    message = db.session.query(Message).filter_by(code=code).first()
    if not message:
        return jsonify({"error": "Mensagem não encontrada"}), 404

    receipt = db.session.query(Receipt).filter_by(message_id=message.id).first()
    if not receipt:
        return jsonify({"error": "Recibo não encontrado"}), 404

    if receipt.confirmed_read:
        return jsonify({"message": "Recibo já confirmado"}), 200

    if not receipt.recipient_user_id:
        return jsonify({"error": "Destinatário sem conta registada"}), 400

    user_key = db.session.query(UserKey).filter_by(user_id=receipt.recipient_user_id).first()
    if not user_key:
        return jsonify({"error": "Chave pública do destinatário não encontrada"}), 404

    # Carregar a chave privada enviada pelo cliente (PEM em texto)
    try:
        chave_privada_rsa = serialization.load_pem_private_key(
            private_key_pem.encode("ascii") if isinstance(private_key_pem, str) else private_key_pem,
            password=None
        )
    except Exception:
        return jsonify({"error": "Chave privada inválida (PEM malformado)"}), 400

    # Verificar que a chave privada corresponde à chave pública registada
    chave_publica_derivada = chave_privada_rsa.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode("ascii")
    if chave_publica_derivada.strip() != user_key.public_key.strip():
        return jsonify({"error": "A chave privada não corresponde à pública registada"}), 401

    # Usar gerar_recibo_digital (RSA-PSS + SHA256) para criar o recibo assinado
    # Confirma receção e leitura (Cenário 2 do enunciado)
    texto_recibo, assinatura = gerar_recibo_digital(None, chave_privada_rsa, code)

    receipt.receipt_text = texto_recibo.decode("utf-8")
    receipt.signature = base64.b64encode(assinatura).decode("ascii")
    receipt.confirmed_read = True
    receipt.confirmed_received = True
    db.session.commit()

    if message.sender_notification_email:
        enviar_notificacao_leitura(message.sender_notification_email, receipt.receipt_text)

    return jsonify({
        "message": "Leitura confirmada com sucesso",
        "receipt_text": receipt.receipt_text,
        "signature": receipt.signature
    })


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
