# Como testar o ServicoEmail

## Permissões (primeira vez)

```bash
sudo usermod -aG docker $USER
newgrp docker
```

## Ligar o Mailpit

```bash
cd ServicoEmail
docker-compose up -d
```

## Correr o teste de envio

```bash
pytest backend/tests/test_email.py -v
```

Verificar emails em: <http://localhost:8025>
