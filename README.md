# Descrição
Projeto no âmbito da UC da UBI: Segurança Informática.

## Estrutura do Projeto
```text
SI_Ok_Eu_CONFESSO/
│
├── backend/
│   ├── app/
│   │   ├── __init__.py          # Inicializa a App e regista Blueprints
│   │   ├── config.py            # Configurações globais
│   │   ├── extensions.py        # SQLAlchemy e Flask-Migrate
│   │   ├── models.py            # Modelos BD (User, UserKey, Message, Receipt)
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py          # /api/auth/register, /api/auth/login
│   │   │   ├── messages.py      # /api/messages/send, /api/messages/decrypt
│   │   │   └── receipts.py      # /api/receipts/verify
│   │   └── services/
│   │       ├── crypto.py        # Primitivas (AES-CTR, RSA, PBKDF2)
│   │       ├── email.py         # Envio de emails local (Mailpit)
│   │       └── auth.py          # Registo e autenticação (Hashes e validação)
│   │
│   ├── tests/
│   │   ├── conftest.py          # Fixtures do Pytest
│   │   ├── test_crypto.py       # Cobertura sobre encriptação AES e RSA
│   │   ├── test_register.py     # Integração do registo e chaves
│   │   └── test_email.py        # Cobertura do sistema de alertas mailpit
│   │
│   ├── instance/
│   │   └── app.db               # Base de dados SQLite (Local Development)
│   ├── migrations/              # Controlo de versões (Alembic)
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Register.jsx     # Permite criar e gerar uma passe
│   │   │   ├── Login.jsx        # Efetua autenticação
│   │   │   ├── SendMessage.jsx  # Pág. de envio seguro de mensagens
│   │   │   └── DecryptMessage.jsx # Desencriptar e ler com código alertado
│   │   ├── services/
│   │   │   └── api.js           # Endpoints Fetch API (Ligação Frontend-Backend)
│   │   ├── index.css            # Estilos tail-made
│   │   └── App.jsx
│   ├── package.json
│   └── vite.config.js           # Server Web com Proxy /api para o Backend (Porta 5000)
│
├── ServicoEmail/                
│   └── docker-compose.yml       # Ferramenta para intercetar o e-mail de mensagens Cifradas (Mailpit)
├── .gitignore
└── README.md
```

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
