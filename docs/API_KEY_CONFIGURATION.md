# API Key - NEF API AD

## 1. Objetivo
A API Key é utilizada para proteger todas as requisições da NEF API AD. Ela deve ser enviada no header `X-API-KEY` em cada chamada à API, garantindo autenticação e segurança.

## 2. Gerar nova API Key

O script responsável pela geração da chave está localizado em:

```
tools/generate_api_key.sh
```

Para gerar uma nova chave, execute o script no servidor:

```
cd /opt/nef-api-ad
./tools/generate_api_key.sh
```

O script utiliza o comando:

```
openssl rand -hex 32
```

Exemplo de saída:

```
4e2f1a8b9c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f
```

## 3. Configurar a API Key no Apache

O arquivo de configuração do VirtualHost da API está em:

```
/etc/apache2/sites-available/nef-api-8025.conf
```

Edite o arquivo com:

```
nano /etc/apache2/sites-available/nef-api-8025.conf
```

Adicione a linha abaixo dentro do bloco `<VirtualHost *:8025>`:

```
SetEnv API_KEY "SUA_CHAVE_GERADA"
```

Substitua `SUA_CHAVE_GERADA` pela chave gerada no passo anterior.

## 4. Reiniciar o Apache

Após configurar a chave, reinicie o Apache obrigatoriamente:

```
systemctl restart apache2
```

## 5. Validar funcionamento

Teste a API com a chave:

```
curl -H "X-API-KEY: SUA_CHAVE" \
     http://127.0.0.1:8025/api/users/list.cgi
```

Teste sem a chave (deve bloquear):

```
curl http://127.0.0.1:8025/api/users/list.cgi
```

## 6. Estrutura de validação no projeto

A validação da API Key ocorre em:

```
lib/common.sh
```

Função responsável:

```
validate_api_key()
```

Todos os scripts CGI chamam essa função após `validate_ldap_config`.

## 7. Boas práticas

- Nunca versionar a chave no Git
- Trocar a chave periodicamente
- Não compartilhar externamente
- Reiniciar Apache após alteração da chave
- Manter permissão segura do arquivo VirtualHost

---

Este documento é destinado ao uso interno da equipe de TI. Siga as recomendações para garantir a segurança da NEF API AD.
