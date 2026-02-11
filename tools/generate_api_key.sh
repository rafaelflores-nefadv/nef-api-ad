#!/bin/bash
set -euo pipefail

# Verifica se openssl está instalado
if ! command -v openssl >/dev/null 2>&1; then
  echo "Erro: openssl não está instalado. Instale openssl para gerar a chave." >&2
  exit 1
fi

# Gera a chave (64 caracteres hex)
API_KEY=$(openssl rand -hex 32)

cat <<EOF
====================================
NEF API KEY GENERATED
====================================
Key: $API_KEY
------------------------------------
Add this to your VirtualHost:

SetEnv API_KEY "$API_KEY"
====================================

Use this key in header:
X-API-KEY: $API_KEY
EOF
