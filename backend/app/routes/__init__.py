from flask import Blueprint

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")
messages_bp = Blueprint("messages", __name__, url_prefix="/api/messages")
receipts_bp = Blueprint("receipts", __name__, url_prefix="/api/receipts")

from . import auth, messages, receipts
