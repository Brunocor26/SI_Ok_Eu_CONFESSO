# Arquitetura — Módulos e Responsabilidades

```mermaid
graph TB
    subgraph FRONTEND["Frontend (React)"]
        REG["Register.jsx\nUI de registo\nMostra password + download chaves"]
        LOG["Login.jsx\nDeriva user_id = SHA-256(pwd)\nAutentica utilizador"]
        SEND["SendMessage.jsx\nFormulário de envio"]
        DEC["DecryptMessage.jsx\nOrquestra 4 passos\nAssina recibo localmente"]
        VER["VerifyReceipt.jsx\nVerifica estado do recibo"]
        API["api.js\nCentraliza chamadas HTTP"]
    end

    subgraph BACKEND["Backend (Flask)"]
        subgraph ROUTES["Routes"]
            RAUTH["routes/auth.py\nGera password + identifier\nRegisto e login"]
            RMSG["routes/messages.py\nEnvio e decifragem"]
            RREC["routes/receipts.py\nRecibos de receção e leitura"]
        end

        subgraph SERVICES["Services"]
            SAUTH["services/auth.py\nLógica de autenticação\nCriação de utilizadores"]
            SCRYP["services/crypto.py\nAES-256-CTR · PBKDF2\nHMAC · RSA · SHA-256"]
            SEMAIL["services/email.py\nEnvio via SMTP/Mailpit"]
        end

        subgraph DB["Base de Dados"]
            USER["User\nuser_id · password_hash · salt"]
            UKEY["UserKey\npublic_key · encrypted_private_key"]
            MSG["Message\nencrypted_body · code · hmac"]
            REC["Receipt\nconfirmed_received · confirmed_read\nreceipt_text · signature"]
        end
    end

    REG & LOG & SEND & DEC & VER --> API
    API --> RAUTH & RMSG & RREC
    RAUTH --> SAUTH --> USER & UKEY
    RAUTH --> SCRYP
    RMSG --> SAUTH
    RMSG --> SCRYP
    RMSG --> SEMAIL
    RMSG --> MSG & REC
    RREC --> SCRYP
    RREC --> REC & UKEY
```

## Responsabilidades

| Módulo | Responsabilidade |
| --- | --- |
| `Register.jsx` | UI de registo; mostra password gerada e faz download das chaves |
| `Login.jsx` | Deriva `user_id = SHA-256(password)` localmente antes de autenticar |
| `SendMessage.jsx` | Formulário de envio de mensagem cifrada |
| `DecryptMessage.jsx` | Orquestra os 4 passos; assina recibo com Web Crypto API sem enviar chave privada |
| `VerifyReceipt.jsx` | Permite ao emissor verificar se a mensagem foi lida e se a assinatura é válida |
| `api.js` | Centraliza todas as chamadas HTTP; lança erro se resposta não for 2xx |
| `routes/auth.py` | Gera password + identifier no registo; cria sessão no login |
| `routes/messages.py` | Cifra e guarda mensagens; decifra e gera receipt_text |
| `routes/receipts.py` | Confirma receção e leitura; verifica assinatura RSA do recibo |
| `services/auth.py` | Cria utilizadores na BD; verifica credenciais com PBKDF2 |
| `services/crypto.py` | Toda a criptografia: AES-256-CTR, PBKDF2, HMAC, RSA, SHA-256 |
| `services/email.py` | Envia email com código e corpo cifrado via SMTP |
| `models.py` | Define User, UserKey, Message, Receipt (SQLAlchemy) |
