# Descrição
Projeto no âmbito da UC da UBI: Segurança Informática.

## Tarefas

| Tarefa | Responsável | Descrição | Critério de Conclusão | Concluído |
|--------|-------------|-----------|----------------------|-----------|
| Escolher stack e ferramentas | Todos | Reunião: linguagem, framework, BD, biblioteca crypto. | Stack documentado e aprovado por todos | ✅ |
| Configurar repo GitHub | @Brunocor26 | Criar organização/repo, GitHub Projects/Issues, regras de PR | Todos com acesso e primeira Issue criada | ✅  |
| Arquitetura e diagramas | @AlexandreMinhoto | Diagrama de componentes, fluxo completo de cifragem/decifragem, diagrama de sequência dos cenários 1 e 2 | Documento de arquitetura (1-2 pág.) no repo | ⬜ |
| Schema da base de dados | @DanielBasilioFerreira | Desenhar tabelas: users, messages, receipts, public_keys. Validar com Bruno | Schema ER aprovado, comentado no repo | ⬜ |
| Wireframes das páginas | @henriquelaia | Esboços de: registo, login, envio, decifra (confirmação dupla), verificar recibo | Wireframes aprovados em reunião | ✅ |
| Configurar serviço de email | @Francisco-Branco-2 | Instalar MailHog/Mailpit, testar envio de email local, definir template base | Email de teste enviado e recebido | ⬜ |
| PoC das primitivas crypto | @Vascorc | Provas de conceito: AES-256-CTR, PBKDF2, SHA256withRSA, AES-256-CBC para chave privada | Cada primitiva testada individualmente | ⬜ |
| Criar estrutura de testes | @Brunocor26 | Configurar framework de testes, criar primeiros testes unitários esqueleto, definir formato de relatório | Framework de testes a correr (mesmo que vazia) | ⬜ |

## Estrutura planeada do projeto

SI_Ok_Eu_CONFESSO/
│
├── backend/
│   ├── app/
│   │   ├── __init__.py          # create_app(), inicializa Flask
│   │   ├── config.py            # configurações (dev, test, prod)
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── user.py          # tabela users
│   │   │   ├── message.py       # tabela messages
│   │   │   ├── receipt.py       # tabela receipts
│   │   │   └── public_key.py    # tabela public_keys
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py          # /register, /login
│   │   │   ├── messages.py      # /send, /decrypt
│   │   │   └── receipts.py      # /confirm, /verify
│   │   ├── services/
│   │   │   ├── crypto.py        # AES, RSA, PBKDF2, HMAC
│   │   │   ├── email.py         # envio de emails
│   │   │   └── receipt.py       # geração e verificação de recibos
│   │   └── utils/
│   │       └── helpers.py       # funções auxiliares genéricas
│   │
│   ├── tests/
│   │   ├── conftest.py          # fixtures globais
│   │   ├── test_crypto.py       # testes das primitivas crypto
│   │   ├── test_auth.py         # testes de registo/login
│   │   ├── test_messages.py     # testes de envio/decifragem
│   │   └── test_receipts.py     # testes de recibos
│   │
│   ├── migrations/              # Flask-Migrate (gerado automaticamente)
│   ├── requirements.txt
│   ├── .env.example
│   └── run.py                   # ponto de entrada: flask run
│
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Register.jsx     # página de registo
│   │   │   ├── Login.jsx        # página de login
│   │   │   ├── SendMessage.jsx  # página de envio
│   │   │   ├── DecryptMessage.jsx # página de decifragem + confirmação dupla
│   │   │   └── VerifyReceipt.jsx  # página de verificação de recibo
│   │   ├── components/          # componentes reutilizáveis
│   │   ├── services/
│   │   │   └── api.js           # chamadas à API Flask
│   │   └── App.jsx
│   ├── package.json
│   └── vite.config.js
│
├── .gitignore
├── README.md
└── docker-compose.yml           # opcional: PostgreSQL + Mailpit

## ⚙️ Setup e Instalação

### Pré-requisitos
- Python 3.12+
- Node.js 18+
- PostgreSQL
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


### 4. Configurar a base de dados


### 5. Configurar o frontend (React)


### 6. Iniciar o Mailpit (email local)


### 7. Correr a aplicação
```bash
# Terminal 1 - Backend
source venv/bin/activate

...
```

### 8. Correr os testes
```bash
source venv/bin/activate
pytest
pytest --cov=app    # com relatório de cobertura
```

---

### URLs locais
| Serviço | URL |
|---|---|
| Frontend | - |
| Backend API | - |
| Mailpit | - |