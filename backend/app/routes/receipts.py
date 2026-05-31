import base64
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding as asym_padding

from flask import request, jsonify
from app.routes import receipts_bp
from app.models import Message, Receipt, UserKey
from app.extensions import db
from app.services.email import enviar_notificacao_leitura


# ---------------------------------------------------------------------------
# Funções auxiliares de assinatura — toda a lógica de assinatura RSA vive aqui (SHA256withRSA)
# O nome de algoritmo "SHA256withRSA" na especificação significa RSA + PKCS1v15 + SHA-256.
# ---------------------------------------------------------------------------

def assinar_recibo(texto_recibo: str, private_pem: str) -> str:
    """Assina o texto do recibo com SHA256withRSA (PKCS1v15 + SHA-256).

    A chave privada só é usada no lado do cliente (browser). Esta função auxiliar
    no servidor é mantida aqui para utilitários de teste e uso futuro, mas NÃO
    é chamada durante o tratamento normal de pedidos — a assinatura é feita no browser.

    Devolve a assinatura como uma string em base64.
    """
    private_key = serialization.load_pem_private_key(
        private_pem.encode("ascii"),
        password=None,
    )
    signature = private_key.sign(
        texto_recibo.encode("utf-8"),
        asym_padding.PKCS1v15(),
        hashes.SHA256(),
    )
    return base64.b64encode(signature).decode("ascii")


def verificar_recibo_leitura(texto_recibo: str, assinatura, chave_publica) -> bool:
    """Verifica a assinatura do recibo usando SHA256withRSA (PKCS1v15 + SHA-256).

    Conforme especificado pelo enunciado: "gera uma assinatura SHA256withRSA do
    recibo de leitura."

    Aceita a chave pública como string PEM (da BD) ou como objeto de chave carregado.
    Aceita a assinatura como string em base64 ou bytes brutos.
    """
    try:
        # Normalizar assinatura → bytes
        if isinstance(assinatura, str):
            assinatura_bin = base64.b64decode(assinatura)
        else:
            assinatura_bin = assinatura

        # Normalizar chave pública → objeto de chave RSA carregado
        if isinstance(chave_publica, str):
            chave_publica_rsa = serialization.load_pem_public_key(chave_publica.encode("ascii"))
        else:
            chave_publica_rsa = chave_publica

        # SHA256withRSA = PKCS1v15 + SHA-256
        chave_publica_rsa.verify(
            assinatura_bin,
            texto_recibo.encode("utf-8") if isinstance(texto_recibo, str) else texto_recibo,
            asym_padding.PKCS1v15(),
            hashes.SHA256(),
        )
        return True  # Assinatura legítima!
    except Exception:
        return False  # Assinatura inválida ou recibo alterado!


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@receipts_bp.route("/verify", methods=["POST"])
def verify_receipt():
    """Confirma que o destinatário recebeu a mensagem (passo 1 de 2)."""
    # 1. Obter o código do corpo da requisição
    data = request.get_json()
    if not data or not data.get("code"):
        return jsonify({"error": "Código em falta"}), 400

    code = data["code"]
    
    # 2. Procurar a mensagem associada ao código
    message = db.session.query(Message).filter_by(code=code).first()
    if not message:
        return jsonify({"error": "Mensagem não encontrada"}), 404

    # 3. Procurar o recibo associado a essa mensagem e marcar como recebido
    receipt = db.session.query(Receipt).filter_by(message_id=message.id).first()
    if receipt:
        receipt.confirmed_received = True
        db.session.commit()

    return jsonify({"message": "Receção confirmada com sucesso!"})


@receipts_bp.route("/check", methods=["POST"])
def check_receipt():
    """Devolve o estado atual de um recibo, incluindo a validade da assinatura."""
    # 1. Extrair o código da mensagem
    data = request.get_json()
    if not data or not data.get("code"):
        return jsonify({"error": "Código em falta"}), 400

    code = data["code"]
    
    # 2. Encontrar a mensagem e o recibo correspondente
    message = db.session.query(Message).filter_by(code=code).first()
    if not message:
        return jsonify({"error": "Mensagem não encontrada"}), 404

    receipt = db.session.query(Receipt).filter_by(message_id=message.id).first()

    # 3. Se não houver recibo gerado ainda, retorna tudo como falso
    if not receipt:
        return jsonify({
            "read": False,
            "confirmed_received": False,
            "signature_valid": False,
            "receipt_text": None,
        })

    # 4. Validar a assinatura se o recibo já foi lido e assinado
    signature_valid = False
    if receipt.confirmed_read and receipt.signature and receipt.receipt_text:
        if receipt.recipient_user_id:
            # Recuperar a chave pública do destinatário para a verificação
            user_key = db.session.query(UserKey).filter_by(user_id=receipt.recipient_user_id).first()
            if user_key:
                # Realiza a verificação usando a função auxiliar
                signature_valid = verificar_recibo_leitura(
                    receipt.receipt_text, receipt.signature, user_key.public_key
                )

    return jsonify({
        "read": receipt.confirmed_read,
        "confirmed_received": receipt.confirmed_received,
        "signature_valid": signature_valid,
        "receipt_text": receipt.receipt_text if receipt.confirmed_read else None,
    })


@receipts_bp.route("/submit-signature", methods=["POST"])
def submit_signature():
    """Recebe e verifica a assinatura SHA256withRSA produzida no browser do destinatário.

    A chave privada nunca chega ao servidor. O frontend assina o receipt_text
    localmente (SHA256withRSA = RSASSA-PKCS1-v1_5 + SHA-256) e envia apenas a
    assinatura resultante em base64. O backend verifica contra a chave pública
    armazenada e, se for válida, guarda-a na BD.
    """
    # 1. Obter a assinatura e o código originados do browser do utilizador
    data = request.get_json()
    if not data or not data.get("code") or not data.get("signature"):
        return jsonify({"error": "Código e assinatura são obrigatórios"}), 400

    code = data["code"]
    signature_b64 = data["signature"]

    # 2. Localizar os registos de mensagem e recibo
    message = db.session.query(Message).filter_by(code=code).first()
    if not message:
        return jsonify({"error": "Mensagem não encontrada"}), 404

    receipt = db.session.query(Receipt).filter_by(message_id=message.id).first()
    if not receipt:
        return jsonify({"error": "Recibo não encontrado"}), 404

    # 3. Garantir que a mensagem já foi decifrada (passo anterior obrigatório)
    if not receipt.receipt_text:
        return jsonify({"error": "Texto do recibo ainda não gerado. Decifra a mensagem primeiro."}), 400

    if not receipt.recipient_user_id:
        return jsonify({"error": "Destinatário não identificado no recibo"}), 400

    # 4. Encontrar a chave pública na BD (a chave privada já não existe do lado do backend)
    user_key = db.session.query(UserKey).filter_by(user_id=receipt.recipient_user_id).first()
    if not user_key:
        return jsonify({"error": "Chave pública do destinatário não encontrada"}), 404

    # 5. Verifica a assinatura SHA256withRSA contra o receipt_text e chave pública guardados
    is_valid = verificar_recibo_leitura(receipt.receipt_text, signature_b64, user_key.public_key)

    if not is_valid:
        return jsonify({"error": "Assinatura inválida: não corresponde à chave pública registada"}), 400

    # 6. Se a assinatura for válida, guardar permanentemente na base de dados
    receipt.signature = signature_b64
    receipt.signature_algorithm = "SHA256withRSA"
    receipt.confirmed_read = True
    db.session.commit()

    # 7. Notificar o emissor por email (se tiver indicado email de notificação)
    if message.sender_notification_email:
        enviar_notificacao_leitura(message.sender_notification_email, receipt.receipt_text)

    return jsonify({"message": "Assinatura SHA256withRSA verificada e guardada com sucesso!"})
