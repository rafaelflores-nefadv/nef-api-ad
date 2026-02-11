# NEF API - Documentação

Visão geral
- Projeto: API simples exposta via scripts CGI em Bash para integração com LDAP/AD e Samba.
- Local dos scripts: `cgi-bin/users` e `cgi-bin/groups` (executáveis CGI).

Formato de resposta JSON
- Todas as respostas usam o formato definido em `cgi-bin/lib/common.sh`:

- Sucesso:

  {"success": true, "data": <obj|arr|null>, "error": null}

- Erro:

  {"success": false, "data": null, "error": "mensagem de erro"}

Requisitos / Dependências
- Sistema com Bash (`/usr/bin/env bash`).
- `ldapsearch` (ldap-utils / openldap-clients).
- `samba-tool` (Samba AD utilities) quando utilizado para criação/edição de contas/grupos.
- `jq` para manipulação JSON.
- `logger` (syslog) para logs.

Variáveis de ambiente necessárias
- `LDAP_URI` - URI do servidor LDAP (ex: ldap://ad.example.com).
- `BIND_DN` - DN de bind para operações LDAP.
- `BIND_PW` - Senha do bind (veja nota de segurança abaixo).
- `BASE_DN` - DN base para buscas.
- `USERS_OU` - OU base para usuários (ex: OU=Users,DC=example,DC=com).
- `GROUPS_OU` - OU base para grupos (alguns scripts assumem essa variável; adicionar se necessário).

Observação: alguns scripts validarão essas variáveis via `validate_ldap_config()` em `common.sh`.

Endpoints / Scripts
- `GET /cgi-bin/users/list.cgi`
  - Descrição: lista todos os usuários encontrados sob `USERS_OU`.
  - Request: nenhum corpo; pode ser chamada como GET CGI.
  - Response (data): lista de objetos `{cn, sAMAccountName, mail, status}` ordenada por `cn`.

- `POST /cgi-bin/users/create.cgi`
  - Descrição: cria um usuário via `samba-tool user create`.
  - Request: JSON no corpo (lido via stdin). Campos:
    - `username` (obrigatório)
    - `password` (obrigatório)
    - `givenName`, `sn`, `mail` (opcionais)
  - Response (data): objeto com `username` e `message` em sucesso.

- `GET /cgi-bin/groups/list.cgi`
  - Descrição: lista grupos sob `GROUPS_OU` (construído com `GROUPS_OU,$BASE_DN`).
  - Request: nenhum corpo.
  - Response (data): array de objetos `{cn, description, memberCount}`.

- `POST /cgi-bin/groups/create.cgi`
  - Descrição: cria um grupo via `samba-tool group add`.
  - Request: JSON no corpo com campos:
    - `groupname` (obrigatório)
    - `description` (opcional)
  - Response (data): objeto com `groupname` e `message` em sucesso.

Outros scripts
- A árvore do projeto contém outros scripts em `cgi-bin/users` e `cgi-bin/groups` como `get.cgi`, `edit.cgi`, `enable.cgi`, `disable.cgi`, `add_member.cgi`, `remove_member.cgi` etc. Estes seguem padrões similares: leitura de JSON via stdin (para operações de mutação) ou leitura de `QUERY_STRING` (para buscas).

Exemplos rápidos
- Exemplo: listar usuários (curl)

```bash
curl -s -X GET 'http://<host>/cgi-bin/users/list.cgi'
```

- Exemplo: criar usuário

```bash
curl -s -X POST 'http://<host>/cgi-bin/users/create.cgi' \
  -H 'Content-Type: application/json' \
  -d '{"username":"jdoe","password":"Secret123!","givenName":"John","sn":"Doe","mail":"jdoe@example.com"}'
```

Formato de logs
- Os scripts usam `logger -t "nef-api-ad"` para registrar ações principais como `USER_CREATE`, `USER_LIST`, `GROUP_CREATE`.

Notas de segurança e recomendações
- Evitar passar senhas em argumentos de linha de comando: comandos como `ldapsearch -w "$BIND_PW"` e `samba-tool user create $username $password` expõem senhas via lista de processos (`ps`). Preferir leitura de senha por stdin, ficheiros temporários com permissões restritas, ou usar APIs/SDKs que não exponham credenciais no processo.
- Evitar `eval`: alguns scripts montam `samba_cmd` e executam com `eval`, o que abre vetor de command injection se entradas do usuário não forem cuidadosamente validadas. Use arrays de argumentos e chame comandos diretamente, por exemplo:

```bash
cmd=(samba-tool user create "${username}" "${password}")
cmd+=(--given-name "${givenName}")
"${cmd[@]}"
```

- Sanitização e validação de entrada: validar formatos esperados (nomes, e-mails) antes de passá-los a comandos do sistema.
- Escapar/serializar mensagens JSON: usar `jq -Rn --arg msg "..." '{success:false, data:null, error:$msg}'` ou `jq -Rs .` para garantir JSON válido e escapar caracteres especiais nas mensagens de erro.
- Validar todas as variáveis de ambiente usadas (adicionar `GROUPS_OU` em `validate_ldap_config`), e falhar rápido com mensagem clara se estiverem ausentes.
- Logging: não logar senhas ou dados sensíveis. Ajustar `log_action` para filtrar/omití-los.
- Adicionar `shellcheck` e políticas de CI para checar scripts Shell automaticamente.

Implantação e permissões
- Configurar o servidor HTTP (ex: Apache, nginx+fcgi) para executar os scripts CGI com o usuário adequado.
- Garantir permissões de ficheiro restritas (`chmod 750` / propriedade apropriada).
- Garantir que ficheiros que contenham credenciais (se usados) tenham `chmod 600` e proprietário restrito.

Checklist de melhoria (prioridade sugerida)
1. Substituir `eval` por chamadas seguras sem `eval` (alta).
2. Evitar passar senhas na linha de comando (alta).
3. Tornar mensagens JSON robustas (usar `jq` para montar respostas) (média).
4. Adicionar validação de `GROUPS_OU` em `common.sh` (baixa).
5. Rodar `shellcheck` e corrigir avisos (média).
6. Documentar operações restantes (`get`, `edit`, `add_member`, `remove_member`) conforme necessário (média).

Onde está a documentação
- Arquivo único: [docs/API.md](docs/API.md)

Próximo passo sugerido
- Se quiser, aplico automaticamente mudanças seguras mínimas (ex.: atualizar `validate_ldap_config`, remover `eval` em scripts `create`) e/ou adiciono `shellcheck` no CI. Diga qual ação prefere.
