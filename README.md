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
│   │   │   ├── auth.py           # POST /register, /login, /logout  |  GET /me
│   │   │   ├── messages.py       # POST /send, /decrypt
│   │   │   └── receipts.py       # POST /verify, /check
│   │   │
│   │   └── services/             # Lógica de negócio desacoplada das rotas
│   │       ├── crypto.py         # Todas as primitivas criptográficas (ver secção abaixo)
│   │       ├── auth.py           # Registo de utilizadores e verificação de credenciais
│   │       └── email.py          # Construção e envio do email cifrado via SMTP
│   │
│   ├── tests/
│   │   ├── conftest.py           # Fixtures Pytest: app em memória e cliente de teste
│   │   ├── test_crypto.py        # 26 testes das primitivas criptográficas
│   │   ├── test_register.py      # Fluxo completo de registo e geração de chaves RSA
│   │   ├── test_cypher.py        # Teste de cifra e decifra de mensagem
│   │   └── test_email.py         # Integração com o Mailpit
│   │
│   ├── migrations/               # Migrações Alembic (controlo de versão do esquema BD)
│   └── instance/app.db           # Base de dados SQLite (gerada automaticamente)
│
├── frontend/                     # Interface web em React + Vite
│   └── src/
│       ├── App.jsx               # Router e guarda de autenticação (AuthGuard)
│       ├── pages/
│       │   ├── Register.jsx      # Gera password de 16 chars e descarrega chaves RSA
│       │   ├── Login.jsx         # Autenticação apenas por password
│       │   ├── SendMessage.jsx   # Formulário de envio de mensagem cifrada
│       │   ├── DecryptMessage.jsx# Fluxo de decifração em 5 passos com confirmação dupla
│       │   └── VerifyReceipt.jsx # Verificação do recibo e validação da assinatura RSA
│       ├── components/
│       │   └── Layout.jsx        # Shell da aplicação: cabeçalho, navegação, rodapé
│       └── services/
│           └── api.js            # Wrapper fetch para todos os endpoints do backend
│
├── ServicoEmail/
│   └── docker-compose.yml        # Mailpit: servidor SMTP (:1025) e interface web (:8025)
│
├── SchemasBD/
│   └── schema.sql                # Esquema SQL das 4 tabelas (referência)
│
├── ProvasDeConceito/             # Scripts Python autónomos para validar primitivas
│   ├── AES-256-CBC.py
│   ├── AES-256-CTR.py
│   ├── PBKDF2.py
│   └── SHA256withRSA.py
│
├── requirements.txt              # Dependências Python (Flask, SQLAlchemy, cryptography)
└── README.md
```

---

## Base de Dados

O esquema tem quatro tabelas relacionadas entre si:

| Tabela | Descrição |
|--------|-----------|
| `users` | Contas de utilizador. O `username` é o SHA-256 da password; a password nunca é armazenada em claro — apenas o hash PBKDF2 com salt. |
| `user_keys` | Par de chaves RSA por utilizador. A chave pública é armazenada em PEM. A chave privada é cifrada com AES-256-CBC usando uma chave derivada da password via PBKDF2. |
| `messages` | Mensagens enviadas. O corpo é cifrado com AES-256-CTR; a chave é derivada de um código aleatório de 32 caracteres hexadecimais via PBKDF2 (600 000 iterações). Inclui HMAC-SHA256 para integridade. |
| `receipts` | Estado de receção e leitura de cada mensagem. Quando confirmada, guarda o texto do recibo e a assinatura SHA256withRSA produzida com a chave privada do destinatário. |

---

## Primitivas Criptográficas

Todas implementadas em `backend/app/services/crypto.py` com a biblioteca `cryptography`:

| Operação | Algoritmo | Parâmetros |
|----------|-----------|------------|
| Hash de password | PBKDF2-SHA256 | 600 000 iterações, salt aleatório de 16 bytes |
| Cifra da mensagem | AES-256-CTR | Chave derivada do código via PBKDF2, nonce aleatório de 16 bytes |
| Cifra da chave privada | AES-256-CBC | Chave derivada da password via PBKDF2, IV aleatório de 16 bytes |
| Integridade da mensagem | HMAC-SHA256 | Calculado sobre o corpo cifrado; comparação em tempo constante |
| Assinatura do recibo | SHA256withRSA | RSA-2048, padding PKCS#1 v1.5 |
| Geração de chaves RSA | RSA-2048 | Par gerado no momento do registo |

---

## Fluxo de Utilização

**Envio (Emissor)**

1. O emissor autentica-se com a sua password de 16 caracteres
2. Preenche o endereço de destino, o assunto e o corpo da mensagem
3. O sistema gera um código aleatório de 32 caracteres hexadecimais, deriva uma chave AES-256 via PBKDF2, cifra o corpo com AES-256-CTR e calcula o HMAC-SHA256
4. O email é enviado ao destinatário com o corpo cifrado e o código de acesso

**Leitura (Destinatário)**

1. O destinatário recebe o email e acede à página de decifração
2. Introduz o código, a sua password e o corpo cifrado recebido no email
3. O sistema apresenta duas confirmações explícitas: receção e intenção de leitura
4. Após confirmação, verifica o HMAC, decifra a mensagem e gera um recibo assinado digitalmente com a chave privada do destinatário

**Verificação (Emissor)**

1. O emissor acede à página de verificação e introduz o código da mensagem
2. O sistema devolve o estado do recibo e valida a assinatura SHA256withRSA

## ⚙️ Setup e Instalação

### Pré-requisitos
- Python 3.12+
- Node.js 18+
- Docker (Opcional, mas recomendado para o ambiente de E-mail)
- Git

---

### 1. Clonar o repositório
```bash
git clone https://github.com/Brunocor26/SI_Ok_Eu_CONFESSO.git
cd SI_Ok_Eu_CONFESSO
```

### 2. Configurar o backend (Flask)
```bash
# Criar e ativar ambiente virtual
python3 -m venv venv
source venv/bin/activate        # se for Mac/Linux
venv\Scripts\activate           # caso do Windows

# Instalar as dependências (definidas no requirements.txt)
pip install -r requirements.txt
```

### 3. Configurar variáveis de ambiente
Por omissão, o backend funciona com uma base de dados SQLite local, pelo que não é estritamente necessário configurar variáveis de ambiente para a sua execução inicial. Caso pretenda, pode configurar a variável `SECRET_KEY` ou alterar o `DATABASE_URL` no ficheiro `backend/app/config.py`.

### 4. Configurar a base de dados
Com o ambiente virtual ativado, aplique as migrações para criar e atualizar as tabelas na base de dados (SQLite por omissão):
```bash
cd backend
flask --app app db upgrade
```

### 5. Configurar o frontend (React)
Instale as dependências associadas ao frontend:
```bash
cd frontend
npm install
```

### 6. Iniciar o Mailpit (email local)
Para receber emails num ambiente de desenvolvimento, utilize o Mailpit através do Docker Compose:
```bash
cd ServicoEmail
docker compose up -d
```

### 7. Correr a aplicação
São necessários dois terminais distintos para correr o backend e o frontend.

```bash
# Terminal 1 - Backend
cd backend
source ../venv/bin/activate  # em Windows: ..\venv\Scripts\activate
flask --app app run --debug
```

```bash
# Terminal 2 - Frontend
cd frontend
npm run dev
```

### 8. Correr os testes
```bash
cd backend
pytest tests/
pytest --cov=app tests/    # com relatório de cobertura
```

---

### URLs locais
| Serviço | URL |
|---|---|
| Frontend | http://localhost:5173 |
| Backend API | http://127.0.0.1:5000 |
| Mailpit | http://localhost:8025 |
