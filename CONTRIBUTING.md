# Regras de Contribuição

## Branches

| Branch | Propósito |
|--------|-----------|
| `main` | Código estável, pronto para entrega |
| `dev` | Integração contínua — PRs vão para aqui |
| `feature/<nome>` | Nova funcionalidade |
| `fix/<nome>` | Correção de bug |

**Nunca fazer push direto para `main`.** Todo o trabalho vai para `dev` via Pull Request.

## Fluxo de trabalho

```
main
 └── dev
      ├── feature/login
      ├── feature/cifra-mensagem
      └── fix/erro-decifra
```

1. Criar branch a partir de `dev`: `git checkout -b feature/<nome> dev`
2. Fazer commits com mensagens claras (ver abaixo)
3. Abrir PR de `feature/<nome>` → `dev`
4. Obter pelo menos **1 aprovação** antes de fazer merge
5. Merge de `dev` → `main` apenas em milestones acordados pelo grupo

## Regras de Pull Request

- **Título:** curto e descritivo (`Adicionar autenticação com JWT`)
- **Descrição:** preencher o template obrigatoriamente
- **Tamanho:** PRs pequenos e focados — uma funcionalidade por PR
- **Revisões:** mínimo **1 aprovação** obrigatória; o autor não pode fazer merge do próprio PR
- **Conflitos:** o autor do PR é responsável por resolver conflitos antes do merge
- **Testes:** o CI deve passar antes do merge

## Mensagens de commit

Formato: `<tipo>: <descrição curta>`

| Tipo | Quando usar |
|------|-------------|
| `feat` | Nova funcionalidade |
| `fix` | Correção de bug |
| `docs` | Documentação |
| `test` | Testes |
| `refactor` | Refactoring sem mudança de comportamento |
| `chore` | Tarefas de manutenção (deps, config) |

Exemplos:
```
feat: adicionar cifra AES-256-CTR para mensagens
fix: corrigir verificação de assinatura RSA
docs: atualizar diagrama de arquitetura
```

## Segurança

- **Nunca** colocar chaves, passwords ou secrets no código
- Usar variáveis de ambiente para configuração sensível
- Qualquer dependência nova deve ser justificada na PR

## Resolução de conflitos

Se dois membros editarem o mesmo ficheiro, o autor do PR mais recente resolve o conflito antes de pedir review.
