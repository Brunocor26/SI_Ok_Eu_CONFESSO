# OK-Eu-CONFESSO — Diagramas de Arquitetura

---

## 1. Diagrama de Componentes

```mermaid
graph TB
    U([Utilizador])

    subgraph Frontend["Aplicação Web (Frontend)"]
        UI_REG[Interface de Registo]
        UI_SEND[Interface de Envio de E-mail]
        UI_READ[Interface de Leitura de E-mail]
        UI_VERIFY[Interface de Verificação de Recibo]
    end

    subgraph Backend["Servidor de Aplicação (Backend)"]
        AUTH[Módulo de Autenticação]
        KEY_MGR[Módulo de Gestão de Chaves RSA]
        CIPHER[Módulo de Cifragem\nAES-256-CTR + PBKDF2]
        MAILER[Módulo de Envio de E-mail\nSMTP]
        DECIPHER[Módulo de Decifragem\n+ Geração de Recibo]
        VERIFY_MOD[Módulo de Verificação\nde Assinatura]
    end

    subgraph BD["Base de Dados"]
        DB_USER[(Utilizadores\nhash palavra-passe)]
        DB_PUBKEY[(Chaves Públicas RSA)]
        DB_MSG[(Mensagens / Códigos\nmetadados)]
        DB_RECEIPT[(Recibos de Leitura\nassinaturas SHA256withRSA)]
    end

    U --> UI_REG
    U --> UI_SEND
    U --> UI_READ
    U --> UI_VERIFY

    UI_REG --> AUTH
    UI_SEND --> CIPHER
    UI_SEND --> MAILER
    UI_READ --> DECIPHER
    UI_VERIFY --> VERIFY_MOD

    AUTH --> DB_USER
    AUTH --> KEY_MGR
    KEY_MGR --> DB_PUBKEY

    CIPHER --> DB_MSG
    MAILER -->|e-mail cifrado| U

    DECIPHER --> DB_MSG
    DECIPHER --> DB_RECEIPT
    VERIFY_MOD --> DB_RECEIPT
    VERIFY_MOD --> DB_PUBKEY
```

---

## 2. Fluxo Principal (Vista Geral)

```mermaid
sequenceDiagram
    actor Emissor
    participant Srv as Sistema
    actor Destinatário

    Note over Emissor,Srv: Envio
    Emissor->>Srv: login (password)
    Srv-->>Emissor: sessão autenticada

    Emissor->>Srv: envia(email, assunto, corpo)
    activate Srv
    Note right of Srv: gera código 32-hex<br/>deriva chave PBKDF2<br/>cifra AES-256-CTR<br/>calcula HMAC-SHA256<br/>guarda na BD
    Srv-->>Emissor: código de rastreio
    Srv->>Destinatário: email com corpo cifrado + código
    deactivate Srv

    Note over Destinatário,Srv: Leitura
    Destinatário->>Srv: acede /decrypt<br/>(código + password + corpo cifrado + chave privada .pem)
    activate Srv
    Destinatário->>Srv: confirma receção ✓
    Destinatário->>Srv: confirma leitura ✓
    Note right of Srv: autentica password<br/>valida chave privada vs pública guardada<br/>verifica HMAC<br/>decifra AES-256-CTR<br/>assina recibo SHA256withRSA<br/>guarda na BD
    Srv-->>Destinatário: mensagem em claro
    deactivate Srv

    Note over Emissor,Srv: Verificação
    Emissor->>Srv: verifica código
    activate Srv
    Note right of Srv: valida assinatura RSA<br/>com chave pública do destinatário (BD)
    Srv-->>Emissor: confirmed_read + signature_valid
    deactivate Srv
```

---

## 4. Fluxo Detalhado de Cifragem / Decifragem

```mermaid
flowchart TD
    A([Início — Emissor]) --> B[Fornece: palavra-passe,\ne-mail destino, assunto, corpo]
    B --> C[Sistema autentica\npor hash da palavra-passe]
    C --> D[Gera código aleatório\n32 caracteres hexadecimal]
    D --> E[Deriva chave de 256 bits\nPBKDF2 com código + salt]
    E --> F[Cifra corpo do e-mail\nAES-256-CTR]
    F --> G[Calcula MAC\nda mensagem cifrada]
    G --> H[Guarda código + metadados\nna Base de Dados]
    H --> I[Envia e-mail cifrado\npelo servidor SMTP]
    I --> J([Destinatário recebe\no e-mail cifrado])

    J --> K[Acede ao site\nvia hiperligação]
    K --> L[Fornece: corpo cifrado,\ncódigo de acesso, password\ne chave privada .pem]
    L --> Q1{Confirma receção?\nSim / Não}
    Q1 -- Não --> R([Fluxo termina\nmensagem não é decifrada])
    Q1 -- Sim --> Q2{Confirma leitura?\nSim / Não}
    Q2 -- Não --> R
    Q2 -- Sim --> M[Autentica password\nValida chave privada vs pública guardada]
    M --> N{MAC válido?}
    N -- Não --> ERR([Erro: mensagem adulterada])
    N -- Sim --> O[Deriva chave\nPBKDF2 com código + salt]
    O --> P[Decifra corpo\nAES-256-CTR]
    P --> S[Mostra mensagem\nao destinatário]
    S --> T[Gera recibo assinado\nSHA256withRSA\nchave privada do destinatário]
    T --> U2[Guarda recibo\nna Base de Dados]
    U2 --> V([Emissor pode verificar\no recibo posteriormente])
```

---

## 5. Diagrama de Sequência — Cenário 1: Registo e Envio

```mermaid
sequenceDiagram
    actor Emissor
    participant App as Aplicação Web
    participant Srv as Servidor / BD
    participant SMTP as Servidor SMTP
    actor Destinatário

    rect rgb(213, 232, 240)
        Note over Emissor,Srv: Registo
        Emissor->>App: Clica em "Registar"
        App->>App: Gerar palavra-passe de 16 caracteres (local)
        App->>App: Derivar identificador interno SHA-256(password)
        App->>Srv: Pedido de registo (identificador + password)
        Srv->>Srv: Gerar par de chaves RSA
        Srv->>Srv: Cifrar chave privada com AES-256-CBC (derivada da palavra-passe)
        Srv->>Srv: Guardar hash PBKDF2 da palavra-passe e chave pública
        Srv-->>App: Devolver chave pública + chave privada (plain)
        App-->>Emissor: Mostrar palavra-passe gerada + botões de download das chaves
    end

    rect rgb(255, 242, 204)
        Note over Emissor,SMTP: Envio de E-mail
        Emissor->>App: Fornece: palavra-passe, e-mail destino, assunto, corpo
        App->>Srv: Pedido de envio cifrado
        Srv->>Srv: Autenticar palavra-passe (verificar hash)
        Srv->>Srv: Gerar código aleatório (32 hex chars)
        Srv->>Srv: Derivar chave 256 bits — PBKDF2(código, salt)
        Srv->>Srv: Cifrar corpo com AES-256-CTR
        Srv->>Srv: Calcular MAC da mensagem cifrada
        Srv->>Srv: Guardar código + metadados na BD
        Srv->>SMTP: Enviar e-mail cifrado (corpo cifrado + instrução + código)
        SMTP-->>Destinatário: Entrega do e-mail
        Srv-->>App: Confirmação de envio
        App-->>Emissor: "E-mail enviado com sucesso"
    end
```

---

## 6. Diagrama de Sequência — Cenário 2: Leitura e Recibo

```mermaid
sequenceDiagram
    actor Destinatário
    participant App as Aplicação Web
    participant Srv as Servidor / BD
    actor Emissor

    rect rgb(213, 232, 240)
        Note over Destinatário,Srv: Acesso ao Site
        Destinatário->>App: Clica na hiperligação no e-mail
        App-->>Destinatário: Página de verificação
        Destinatário->>App: Fornece: (i) código, (ii) password, (iii) corpo cifrado, (iv) chave privada .pem
    end

    rect rgb(212, 232, 212)
        Note over Destinatário,Srv: Confirmação Explícita
        App-->>Destinatário: Diálogo 1: "Acusa a receção?" (Sim / Não)
        Destinatário->>App: Sim
        App->>Srv: POST /receipts/verify (código)
        Srv->>Srv: recibo.confirmado_recebido = True
        Srv-->>App: ok
        App-->>Destinatário: Diálogo 2: "Confirma que vai ler?" (Sim / Não)
        Destinatário->>App: Sim
    end

    rect rgb(255, 242, 204)
        Note over App,Srv: Decifragem + Geração do Recibo
        App->>Srv: POST /messages/decrypt (código + password + corpo cifrado + chave privada)
        Srv->>Srv: Autenticar password via PBKDF2
        Srv->>Srv: Validar chave privada vs chave pública guardada na BD
        Srv->>Srv: Verificar HMAC-SHA256
        Srv->>Srv: Derivar chave — PBKDF2(código, salt)
        Srv->>Srv: Decifrar corpo com AES-256-CTR
        Srv->>Srv: Assinar recibo com SHA256withRSA (chave privada fornecida)
        Srv->>Srv: Guardar recibo assinado na BD
        Srv-->>App: assunto + corpo em claro
        App-->>Destinatário: Apresenta a mensagem decifrada
    end

    rect rgb(230, 220, 240)
        Note over Emissor,Srv: Verificação pelo Emissor (opcional)
        Emissor->>App: Verificar recibo (código)
        App->>Srv: POST /receipts/check (código)
        Srv->>Srv: Consultar recibo + chave pública do destinatário na BD
        Srv->>Srv: Validar assinatura SHA256withRSA
        Srv-->>App: confirmed_read + signature_valid + receipt_text
        App-->>Emissor: "Recibo válido — mensagem foi lida"
    end
```
