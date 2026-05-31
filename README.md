# OK — Eu Confesso

Sistema web de mensagens cifradas com recibo de leitura com garantia criptográfica, desenvolvido no âmbito da unidade curricular de Segurança Informática da UBI.

O sistema permite enviar mensagens cujo conteúdo só pode ser lido após o destinatário confirmar explicitamente a receção e a intenção de leitura. Essa confirmação gera um recibo assinado digitalmente que pode ser verificado pelo emissor.

---

## Arquitectura

O sistema é composto por três componentes que correm localmente:

- **Backend** — API REST em Flask que gere autenticação, criptografia e base de dados
- **Frontend** — Interface web em React (Vite) que comunica com o backend via proxy
- **Serviço de Email** — Mailpit, um servidor SMTP local que captura os emails enviados durante o desenvolvimento

```
Frontend (React)  ──/api──►  Backend (Flask)  ──SMTP──►  Mailpit
     :5173                        :5000                    :1025 / :8025
```

---

## Estrutura do Projeto

```text
SI_Ok_Eu_CONFESSO/
│
├── backend/                      # API REST em Flask
│   ├── app/
│   │   ├── __init__.py           # Fábrica da aplicação e registo de blueprints
│   │   ├── config.py             # Configurações (base de dados, chave de sessão)
│   │   ├── extensions.py         # Instâncias partilhadas: SQLAlchemy, Flask-Migrate
│   │   ├── models.py             # Modelos ORM: User, UserKey, Message, Receipt
│   │   │
│   │   ├── routes/               # Endpoints da API (organizados por recurso)
│   │   │   ├── auth.py           # POST /api/auth/register
│   │   │   ├── messages.py       # POST /api/messages/send, /decrypt
│   │   │   └── receipts.py       # POST /api/receipts/verify, /check, /submit-signature
│   │   │
│   │   └── services/             # Lógica de negócio desacoplada das rotas
│   │       ├── crypto.py         # Todas as primitivas criptográficas (ver secção abaixo)
│   │       ├── auth.py           # Registo de utilizadores e verificação de credenciais
│   │       └── email.py          # Construção e envio de emails via SMTP
│   │
│   ├── tests/
│   │   ├── conftest.py           # Fixtures Pytest: app em memória e cliente de teste
│   │   ├── test_crypto.py        # 26 testes unitários das primitivas criptográficas
│   │   ├── test_cypher.py        # Smoke test de cifra/decifra básico
│   │   ├── test_register.py      # Registo de utilizador e geração de chaves RSA
│   │   ├── test_decrypt_route.py # Integração: endpoint /messages/decrypt (fluxo e erros)
│   │   ├── test_fluxo_completo.py# Integração end-to-end: emissor → destinatário → recibo
│   │   └── test_email.py         # Notificações de leitura (mock + Mailpit real)
│   │
│   ├── migrations/               # Migrações Alembic (controlo de versão do esquema BD)
│   ├── requirements.txt          # Dependências Python
│   └── instance/app.db           # Base de dados SQLite (gerada automaticamente)
│
├── frontend/                     # Interface web em React + Vite
│   └── src/
│       ├── App.jsx               # Router principal
│       ├── pages/
│       │   ├── Register.jsx      # Gera password de 16 chars e descarrega chaves RSA
│       │   ├── SendMessage.jsx   # Formulário de envio de mensagem cifrada
│       │   ├── DecryptMessage.jsx# Fluxo de decifração em 4 passos com confirmação dupla
│       │   └── VerifyReceipt.jsx # Verificação do recibo e validação da assinatura RSA
│       ├── components/
│       │   └── Layout.jsx        # Shell da aplicação: navegação e rodapé
│       └── services/
│           └── api.js            # Wrapper fetch para todos os endpoints do backend
│
├── ServicoEmail/
│   └── docker-compose.yml        # Mailpit: SMTP (:1025) e interface web (:8025)
│
├── setup.sh                      # Instala dependências e inicializa a BD (correr uma vez)
├── start.sh                      # Inicia backend, frontend e Mailpit em paralelo
└── README.md
```

---

## Base de Dados

| Tabela | Descrição |
|--------|-----------|
| `users` | Contas de utilizador. O `user_id` é o SHA-256 da password; a password nunca é armazenada em claro — apenas o hash PBKDF2 com salt. |
| `user_keys` | Par de chaves RSA por utilizador. A chave pública é armazenada em PEM. A chave privada é devolvida cifrada (AES-256-CBC/CTR + PBKDF2) para o utilizador guardar localmente. |
| `messages` | Mensagens enviadas. O corpo é cifrado com AES-256-CTR; a chave é derivada de um código aleatório de 32 chars hexadecimais via PBKDF2 (600 000 iterações). Inclui HMAC-SHA256 para integridade. |
| `receipts` | Estado de receção e leitura de cada mensagem. Quando confirmada, guarda o texto do recibo e a assinatura SHA256withRSA produzida com a chave privada do destinatário. |

---

## Primitivas Criptográficas

Implementadas em `backend/app/services/crypto.py` com a biblioteca `cryptography`:

| Operação | Algoritmo | Parâmetros |
|----------|-----------|------------|
| Hash de password | PBKDF2-SHA256 | 600 000 iterações, salt aleatório de 16 bytes |
| Cifra da mensagem | AES-256-CTR | Chave derivada do código via PBKDF2, nonce aleatório de 16 bytes |
| Cifra da chave privada | AES-256-CBC ou AES-256-CTR | Chave derivada da password via PBKDF2, IV aleatório de 16 bytes |
| Integridade da mensagem | HMAC-SHA256 | Calculado sobre o corpo cifrado; comparação em tempo constante |
| Assinatura do recibo | SHA256withRSA | RSA (2048/3072/4096 bits), padding PKCS#1 v1.5, feita no browser |
| Geração de chaves RSA | RSA configurável | Par gerado no momento do registo; tamanho escolhido pelo utilizador |

---

## Fluxo de Utilização

**Registo**

1. O utilizador acede à página de registo e escolhe os parâmetros criptográficos (cifra da chave privada e tamanho RSA)
2. O sistema gera uma password aleatória de 16 caracteres e um par de chaves RSA
3. A chave privada é devolvida cifrada (JSON com metadados PBKDF2 + AES) — o utilizador descarrega e guarda localmente
4. A chave pública fica armazenada no servidor

**Envio (Emissor)**

1. O emissor autentica-se com a sua password de 16 caracteres
2. Preenche o endereço de destino, assunto, corpo da mensagem e, opcionalmente, o seu email para notificação de leitura
3. O sistema gera um código aleatório de 32 chars hex, deriva uma chave AES-256 via PBKDF2, cifra o corpo com AES-256-CTR e calcula o HMAC-SHA256
4. O email é enviado ao destinatário com o corpo cifrado, o código de acesso e o código HMAC

**Leitura (Destinatário)**

1. O destinatário recebe o email e acede à página de decifração
2. Introduz o código, a sua password, o corpo cifrado e carrega o ficheiro da chave privada cifrada
3. O sistema apresenta duas confirmações explícitas: receção e intenção de leitura
4. Após confirmação, o HMAC é verificado, a mensagem é decifrada e o recibo é assinado digitalmente **no browser** com a chave privada (nunca enviada ao servidor)
5. Se o emissor tiver fornecido email de notificação, é-lhe enviado um aviso de leitura

**Verificação (Emissor)**

1. O emissor acede à página de verificação e introduz o código da mensagem
2. O sistema devolve o estado do recibo e valida a assinatura SHA256withRSA

---

## Setup e Instalação

### Pré-requisitos

- Python 3.12+
- Node.js 18+
- Docker (para o Mailpit via docker-compose) **ou** [Mailpit instalado localmente](https://mailpit.axllent.org/docs/install/)

### Instalação (primeira vez)

```bash
git clone https://github.com/Brunocor26/SI_Ok_Eu_CONFESSO.git
cd SI_Ok_Eu_CONFESSO
chmod +x setup.sh start.sh
./setup.sh
```

O `setup.sh` faz automaticamente:
- Cria o virtualenv Python em `backend/.venv`
- Instala as dependências Python (`requirements.txt`)
- Aplica as migrações e inicializa a base de dados SQLite
- Instala as dependências Node (`npm install`)

### Iniciar a aplicação

```bash
./start.sh
```

O `start.sh` inicia em paralelo:
- **Backend** Flask em `http://127.0.0.1:5000`
- **Frontend** Vite em `http://localhost:5173`
- **Mailpit** (se disponível) em `http://localhost:8025`

Parar tudo: `Ctrl+C`

### Mailpit via Docker (alternativa)

Se não tiver o Mailpit instalado localmente:

```bash
cd ServicoEmail
docker compose up -d
```

---

## Testes

A suite de testes corre com SQLite em memória — não afecta a base de dados de desenvolvimento.

### Correr todos os testes

```bash
cd backend
.venv/bin/pytest tests/ -v
```

### Com relatório de cobertura

```bash
.venv/bin/pytest --cov=app tests/
```

### Ficheiros de teste

| Ficheiro | Tipo | Descrição |
|----------|------|-----------|
| `test_crypto.py` | Unitário | 26 testes das primitivas criptográficas: `generate_code`, `derive_key`, `encrypt_body`, `decrypt_body`, `compute_hmac`, `verify_hmac` e fluxos completos |
| `test_cypher.py` | Unitário | Smoke test de cifra e decifra básico |
| `test_register.py` | Integração | Registo via `register_user`: verifica criação do utilizador, geração do par RSA e formato da chave privada cifrada (JSON com metadados PBKDF2) |
| `test_decrypt_route.py` | Integração | Endpoint `POST /api/messages/decrypt`: fluxo feliz, campos em falta, código inválido, corpo adulterado, HMAC adulterado, destinatário sem conta |
| `test_fluxo_completo.py` | Integração end-to-end | Fluxo completo: registo → envio → confirmação de receção → decifração → assinatura do recibo → verificação da assinatura → notificação ao emissor |
| `test_email.py` | Integração + Mailpit | Notificação ao emissor: verifica com mock que a função é chamada com os argumentos certos; verifica sem mock que o email chega ao Mailpit (ignorado automaticamente se o Mailpit não estiver activo) |

### Testes que requerem Mailpit

Os testes `test_notificacao_leitura_chega_ao_mailpit` e `test_envio_email` são ignorados automaticamente (`skipif`) se o Mailpit não estiver acessível em `localhost:1025`. Para os correr:

```bash
# Opção 1 — Mailpit local
mailpit &

# Opção 2 — Docker
cd ServicoEmail && docker compose up -d

# Depois
cd backend
.venv/bin/pytest tests/test_email.py -v
```

---

## URLs locais

| Serviço | URL |
|---------|-----|
| Aplicação | http://localhost:5173 |
| Backend API | http://127.0.0.1:5000 |
| Mailpit (UI) | http://localhost:8025 |
