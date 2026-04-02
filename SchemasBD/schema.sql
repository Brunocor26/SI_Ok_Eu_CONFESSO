-- Users: each account is identified solely by a 16-char password
CREATE TABLE users (
    id                SERIAL PRIMARY KEY,
    password_hash     TEXT        NOT NULL,  -- PBKDF2/bcrypt of the 16-char password
    password_salt     TEXT        NOT NULL,  -- salt for password hashing
    hash_algorithm    TEXT        NOT NULL DEFAULT 'pbkdf2_sha256',
    created_at        TIMESTAMP   NOT NULL DEFAULT NOW()
);

-- User key pairs: public key always stored; private key optionally stored (encrypted)
CREATE TABLE user_keys (
    id                      SERIAL PRIMARY KEY,
    user_id                 INTEGER     NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    public_key              TEXT        NOT NULL,  -- PEM format
    encrypted_private_key   TEXT,                  -- AES-encrypted PEM; NULL if user stores locally
    private_key_iv          TEXT,                  -- IV used to encrypt the private key
    private_key_salt        TEXT,                  -- PBKDF2 salt to derive key-encryption key from password
    key_cipher_algo         TEXT        NOT NULL DEFAULT 'AES-256-CBC',  -- AES-256-CBC or AES-256-CTR
    rsa_key_size            INTEGER     NOT NULL DEFAULT 2048,
    created_at              TIMESTAMP   NOT NULL DEFAULT NOW()
);

-- Messages: body is partially encrypted; code is stored in clear for later receipt verification
CREATE TABLE messages (
    id                SERIAL PRIMARY KEY,
    sender_id         INTEGER     NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    recipient_email   TEXT        NOT NULL,
    subject           TEXT        NOT NULL,
    encrypted_body    TEXT        NOT NULL,  -- base64-encoded AES-encrypted body
    code              TEXT        NOT NULL,  -- random 32-char hex code (included in the e-mail)
    code_salt         TEXT        NOT NULL,  -- PBKDF2 salt to derive the 256-bit cipher key from code
    pbkdf2_iterations INTEGER     NOT NULL DEFAULT 600000,
    cipher_algo       TEXT        NOT NULL DEFAULT 'AES-256-CTR',  -- AES-256-CTR or AES-256-CBC
    iv_nonce          TEXT        NOT NULL,  -- IV / nonce for AES
    hmac              TEXT,                  -- HMAC-SHA256 of encrypted_body (integrity check)
    sent_at           TIMESTAMP   NOT NULL DEFAULT NOW()
);

-- Receipts: confirmation of reception and reading, with a digital signature
CREATE TABLE receipts (
    id                    SERIAL PRIMARY KEY,
    message_id            INTEGER     NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    recipient_email       TEXT        NOT NULL,
    recipient_user_id     INTEGER     REFERENCES users(id) ON DELETE SET NULL,  -- NULL if not registered
    confirmed_received    BOOLEAN     NOT NULL DEFAULT FALSE,
    confirmed_read        BOOLEAN     NOT NULL DEFAULT FALSE,
    receipt_text          TEXT,        -- exact text that was signed
    signature             TEXT,        -- SHA256withRSA signature in base64
    signature_algorithm   TEXT        NOT NULL DEFAULT 'SHA256withRSA',
    created_at            TIMESTAMP   NOT NULL DEFAULT NOW()
);

-- Indexes for common lookups
CREATE INDEX idx_messages_sender    ON messages(sender_id);
CREATE INDEX idx_messages_code      ON messages(code);
CREATE INDEX idx_receipts_message   ON receipts(message_id);
CREATE INDEX idx_user_keys_user     ON user_keys(user_id);
