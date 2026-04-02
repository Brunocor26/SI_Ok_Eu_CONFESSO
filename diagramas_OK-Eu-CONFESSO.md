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

## 2. Fluxo Completo de Cifragem / Decifragem

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
    K --> L[Fornece: corpo cifrado,\ncódigo de acesso,\nchave privada RSA]
    L --> M{MAC válido?}
    M -- Não --> N([Erro: mensagem adulterada])
    M -- Sim --> O[Deriva chave\nPBKDF2 com código + salt]
    O --> P[Decifra corpo\nAES-256-CTR]
    P --> Q{Utilizador confirma\nreceção e leitura?\nSim / Não}
    Q -- Não --> R([Mensagem mostrada\nsem recibo])
    Q -- Sim --> S[Mostra mensagem\nao destinatário]
    S --> T[Gera recibo assinado\nSHA256withRSA\nchave privada do destinatário]
    T --> U2[Guarda recibo\nna Base de Dados]
    U2 --> V([Emissor pode verificar\no recibo posteriormente])
```

---

## 3. Diagrama de Sequência — Cenário 1: Registo e Envio

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
        App->>Srv: Solicitar novo registo
        Srv->>Srv: Gerar palavra-passe de 16 caracteres
        Srv->>Srv: Gerar par de chaves RSA
        Srv->>Srv: Cifrar chave privada com AES-256-CBC (derivada da palavra-passe)
        Srv->>Srv: Guardar hash da palavra-passe e chave pública
        Srv-->>App: Devolver palavra-passe + par de chaves
        App-->>Emissor: Mostrar palavra-passe (16 chars) e entregar chaves
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

## 4. Diagrama de Sequência — Cenário 2: Leitura e Recibo

```mermaid
sequenceDiagram
    actor Destinatário
    participant App as Aplicação Web
    participant Srv as Servidor / BD
    actor Emissor

    rect rgb(213, 232, 240)
        Note over Destinatário,Srv: Acesso ao Site
        Destinatário->>App: Clica na hiperligação no e-mail (https://OK-Eu-CONFESSO.xxx)
        App-->>Destinatário: Página de verificação
        Destinatário->>App: Fornece: (i) corpo cifrado, (ii) código de acesso, (iii) chave privada RSA
    end

    rect rgb(255, 242, 204)
        Note over App,Srv: Decifragem
        App->>Srv: Pedido de decifragem
        Srv->>Srv: Verificar MAC da mensagem
        Srv->>Srv: Derivar chave — PBKDF2(código, salt)
        Srv->>Srv: Decifrar corpo com AES-256-CTR
    end

    rect rgb(212, 232, 212)
        Note over Destinatário,App: Confirmação Explícita
        Srv-->>App: Mensagem decifrada (ainda oculta)
        App-->>Destinatário: Diálogo 1: "Acusa a receção?" (Sim / Não)
        Destinatário->>App: Sim
        App-->>Destinatário: Diálogo 2: "Confirma que vai ler?" (Sim / Não)
        Destinatário->>App: Sim
        App-->>Destinatário: Apresenta a mensagem decifrada
    end

    rect rgb(248, 206, 204)
        Note over App,Srv: Geração do Recibo
        App->>Srv: Gerar recibo de leitura
        Srv->>Srv: Assinar recibo com SHA256withRSA (chave privada do destinatário)
        Srv->>Srv: Guardar recibo assinado na BD
        Srv-->>App: Recibo gerado
        App-->>Destinatário: "Recibo de leitura registado"
    end

    rect rgb(230, 220, 240)
        Note over Emissor,Srv: Verificação pelo Emissor (opcional)
        Emissor->>App: Verificar recibo (fornece chave pública do destinatário)
        App->>Srv: Consultar recibo na BD
        Srv->>Srv: Validar assinatura SHA256withRSA
        Srv-->>App: Resultado da validação
        App-->>Emissor: "Recibo válido — mensagem foi lida"
    end
```
