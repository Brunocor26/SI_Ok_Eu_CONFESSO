# CLAUDE.md — OK, Eu Confesso

Projeto académico da UC **Segurança Informática (UBI)**.  
Sistema web que envia emails parcialmente cifrados e obriga o destinatário a confirmar explicitamente a receção e leitura antes de decifrar a mensagem.

---

## Equipa

| Membro | Responsabilidades |
|---|---|
| **Henrique Laia** (tu) | Wireframes, estrutura de testes, módulo AES-CTR (`crypto.py`), coordenação |
| **Bruno Correia** | Repositório, backend Flask (routes, `__init__.py`), arquitetura |
| **Ruivo** | Diagramas de arquitetura |
| **Daniel** | Schema BD, migrations Flask-Migrate |
| **Francisco** | Serviço de email (Mailpit/SMTP) |
| **Vasco** | PoC crypto: RSA + SHA256withRSA + AES-256-CBC (cifrar chave privada) |

---

## Stack

| Camada | Tecnologia |
|---|---|
| Backend | Python 3.12 + Flask |
| Crypto | `cryptography` (AES-256-CTR/CBC, PBKDF2, HMAC-SHA256, RSA, SHA256withRSA) |
| Frontend | React (Vite) + CSS customizado |
| Base de dados | SQLite (dev) via SQLAlchemy + Flask-Migrate |
| Email | Mailpit (Docker) via SMTP |
| Testes | pytest |

---

## Estrutura do Projeto

```
SI_Ok_Eu_CONFESSO/
├── backend/
│   ├── app/
│   │   ├── __init__.py          # Inicializa Flask e regista Blueprints
│   │   ├── config.py            # Configurações globais
│   │   ├── extensions.py        # SQLAlchemy + Flask-Migrate
│   │   ├── models.py            # User, UserKey, Message, Receipt
│   │   ├── routes/
│   │   │   ├── auth.py          # /api/auth/register, /login, /logout, /me
│   │   │   ├── messages.py      # /api/messages/send, /decrypt
│   │   │   └── receipts.py      # /api/receipts/verify
│   │   └── services/
│   │       ├── crypto.py        # Todas as primitivas criptográficas
│   │       ├── email.py         # Envio de email cifrado via SMTP
│   │       └── auth.py          # Registo e autenticação
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── test_crypto.py       # Cobertura AES-CTR, RSA, PBKDF2, HMAC
│   │   ├── test_register.py     # Integração registo + chaves
│   │   └── test_email.py        # Mailpit
│   ├── decifrar.py              # Script standalone de decifragem
│   ├── instance/app.db          # SQLite (dev)
│   └── migrations/              # Alembic/Flask-Migrate
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Login.jsx        # Login (apenas password 16 chars, sem username)
│   │   │   ├── Register.jsx     # Registo com geração de password
│   │   │   ├── SendMessage.jsx  # [POR CRIAR] Envio seguro de mensagens
│   │   │   └── DecryptMessage.jsx # [POR CRIAR] Decifragem com código
│   │   ├── services/api.js      # Fetch API — liga frontend ao backend
│   │   ├── App.jsx              # Router (login, register; faltam send e decrypt)
│   │   └── index.css
│   ├── package.json
│   └── vite.config.js           # Proxy /api → http://127.0.0.1:5000
├── ServicoEmail/
│   └── docker-compose.yml       # Mailpit
├── ProvasDeConceito/            # PoCs iniciais (AES-CBC, CTR, PBKDF2, RSA)
├── SchemasBD/
├── diagramas_OK-Eu-CONFESSO.md
└── README.md
```

---

## Design Criptográfico

### Envio de mensagem
1. Gera código aleatório de 32 hex chars (`secrets.token_hex(16)`)
2. Gera salt aleatório (16 bytes)
3. Deriva chave 256-bit: `PBKDF2(code, salt, 600_000 iterations, SHA-256)`
4. Cifra corpo: `AES-256-CTR(plaintext, key, random_nonce)`
5. Calcula integridade: `HMAC-SHA256(ciphertext_b64, key)`
6. Guarda na BD: `encrypted_body`, `code`, `code_salt`, `iv_nonce`, `hmac`
7. Envia email com corpo cifrado + código

### Registo de utilizador
- Password de 16 chars gerada pelo sistema
- Username = `SHA-256(password)` derivado no frontend (zero-knowledge, sem username visível)
- Par RSA gerado (2048-bit por omissão)
- Chave privada cifrada: `AES-256-CBC(private_key_pem, PBKDF2(password, salt), PKCS7_padding)`

### Decifragem
- Destinatário fornece o código → backend localiza mensagem → valida HMAC → decifra AES-CTR
- Marca `confirmed_read = True` no recibo

### Recibos digitais
- Modelo `Receipt` com campos: `confirmed_received`, `confirmed_read`, `receipt_text`, `signature` (SHA256withRSA), `signature_algorithm`

---

## Modelos da Base de Dados

| Tabela | Campos chave |
|---|---|
| `users` | `id`, `username` (hash da password), `password_hash`, `password_salt`, `hash_algorithm` |
| `user_keys` | `user_id`, `public_key`, `encrypted_private_key`, `private_key_iv`, `private_key_salt`, `key_cipher_algo` (AES-256-CBC), `rsa_key_size` |
| `messages` | `sender_id`, `recipient_email`, `subject`, `encrypted_body`, `code`, `code_salt`, `pbkdf2_iterations`, `cipher_algo`, `iv_nonce`, `hmac` |
| `receipts` | `message_id`, `recipient_email`, `confirmed_received`, `confirmed_read`, `receipt_text`, `signature`, `signature_algorithm` |

---

## API Endpoints

| Método | Rota | Descrição |
|---|---|---|
| POST | `/api/auth/register` | Regista utilizador (username + password) |
| POST | `/api/auth/login` | Login → cria sessão Flask |
| POST | `/api/auth/logout` | Termina sessão |
| GET | `/api/auth/me` | Retorna utilizador autenticado |
| POST | `/api/messages/send` | Cifra e envia mensagem por email |
| POST | `/api/messages/decrypt` | Decifra mensagem pelo código |
| POST | `/api/receipts/verify` | Confirma receção pelo código |

---

## O que está feito vs. por fazer

### Feito (em `main`)
- [x] Backend Flask completo: app, modelos, routes, serviços
- [x] Primitivas crypto: AES-256-CTR, AES-256-CBC, PBKDF2, HMAC-SHA256, RSA, SHA256withRSA
- [x] Serviço de email (Mailpit)
- [x] Auth: registo + login com sessão Flask
- [x] SQLite + migrações Alembic
- [x] Frontend: `Login.jsx` + `Register.jsx`
- [x] Suite de testes (`test_crypto.py`, `test_register.py`, `test_email.py`)
- [x] Script `decifrar.py` standalone

### Por fazer (gap crítico)
- [ ] **Frontend `SendMessage.jsx`** — formulário para enviar mensagem cifrada (route `/send` existe no backend mas a página não existe)
- [ ] **Frontend `DecryptMessage.jsx`** — formulário para inserir código e decifrar (route `/decrypt` existe no backend mas a página não existe)
- [ ] **App.jsx**: adicionar routes `/send` e `/decrypt`
- [ ] **Confirmação dupla no frontend** — diálogos "confirmas receção?" e "confirmas que vais ler?" antes de mostrar mensagem
- [ ] **Geração de recibo assinado** no fluxo de decifragem (campo `signature` no modelo existe mas não é preenchido)
- [ ] **Página de verificação de recibo** para o emissor ver se a mensagem foi lida (e validar assinatura)

---

## Comandos de Desenvolvimento

```bash
# Backend
cd backend
flask --app app run --debug          # porta 5000

# Frontend
cd frontend
npm run dev                          # porta 5173 com proxy /api → :5000

# Email (Docker)
cd ServicoEmail
docker compose up -d                 # Mailpit em http://localhost:8025

# Testes
cd backend
pytest tests/
pytest --cov=app tests/              # com cobertura

# Migrações
cd backend
flask --app app db upgrade
```

## URLs Locais

| Serviço | URL |
|---|---|
| Frontend | http://localhost:5173 |
| Backend API | http://127.0.0.1:5000 |
| Mailpit | http://localhost:8025 |

---

## Notas Importantes

- O username no sistema é derivado via `SHA-256(password)` no frontend — o utilizador nunca vê ou digita um username (zero-knowledge).
- A chave privada RSA nunca é enviada ao backend em texto-limpo — apenas a versão cifrada com AES-256-CBC é armazenada.
- O código de 32 hex chars é o único "segredo" que viaja no email; sem ele é impossível decifrar.
- O HMAC garante que a mensagem não foi alterada em trânsito ou na BD.
- Commits e mensagens Git não devem fazer referência a ferramentas de IA.
