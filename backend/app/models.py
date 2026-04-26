from datetime import datetime, timezone
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy import String, Integer, DateTime, Boolean, ForeignKey, Text

from .extensions import db


class User(db.Model):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    password_salt: Mapped[str] = mapped_column(Text, nullable=False)
    hash_algorithm: Mapped[str] = mapped_column(String, default="pbkdf2_sha256", server_default="pbkdf2_sha256", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), server_default=db.func.now(), nullable=False)

    user_keys = relationship("UserKey", back_populates="user", cascade="all, delete-orphan")
    messages_sent = relationship("Message", back_populates="sender", cascade="all, delete-orphan")
    receipts = relationship("Receipt", back_populates="recipient_user")


class UserKey(db.Model):
    __tablename__ = "user_keys"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    public_key: Mapped[str] = mapped_column(Text, nullable=False)
    encrypted_private_key: Mapped[str] = mapped_column(Text, nullable=True)
    private_key_iv: Mapped[str] = mapped_column(Text, nullable=True)
    private_key_salt: Mapped[str] = mapped_column(Text, nullable=True)
    key_cipher_algo: Mapped[str] = mapped_column(String, default="AES-256-CBC", server_default="AES-256-CBC", nullable=False)
    rsa_key_size: Mapped[int] = mapped_column(Integer, default=2048, server_default="2048", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), server_default=db.func.now(), nullable=False)

    user = relationship("User", back_populates="user_keys")


class Message(db.Model):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    sender_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    recipient_email: Mapped[str] = mapped_column(Text, nullable=False)
    subject: Mapped[str] = mapped_column(Text, nullable=False)
    encrypted_body: Mapped[str] = mapped_column(Text, nullable=False)
    code: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    code_salt: Mapped[str] = mapped_column(Text, nullable=False)
    pbkdf2_iterations: Mapped[int] = mapped_column(Integer, default=600000, server_default="600000", nullable=False)
    cipher_algo: Mapped[str] = mapped_column(String, default="AES-256-CTR", server_default="AES-256-CTR", nullable=False)
    iv_nonce: Mapped[str] = mapped_column(Text, nullable=False)
    hmac: Mapped[str] = mapped_column(Text, nullable=True)
    sent_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), server_default=db.func.now(), nullable=False)

    sender = relationship("User", back_populates="messages_sent")
    receipts = relationship("Receipt", back_populates="message", cascade="all, delete-orphan")


class Receipt(db.Model):
    __tablename__ = "receipts"

    id: Mapped[int] = mapped_column(primary_key=True)
    message_id: Mapped[int] = mapped_column(ForeignKey("messages.id", ondelete="CASCADE"), nullable=False, index=True)
    recipient_email: Mapped[str] = mapped_column(Text, nullable=False)
    recipient_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    confirmed_received: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0", nullable=False)
    confirmed_read: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0", nullable=False)
    receipt_text: Mapped[str] = mapped_column(Text, nullable=True)
    signature: Mapped[str] = mapped_column(Text, nullable=True)
    signature_algorithm: Mapped[str] = mapped_column(String, default="SHA256withRSA", server_default="SHA256withRSA", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), server_default=db.func.now(), nullable=False)

    message = relationship("Message", back_populates="receipts")
    recipient_user = relationship("User", back_populates="receipts")
