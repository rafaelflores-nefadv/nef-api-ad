#!/usr/bin/env bash
set -u

echo "Content-Type: application/json"
echo ""

source "$(dirname "$0")/../lib/common.sh"
validate_ldap_config

input=$(cat)

sam=$(echo "$input" | jq -r '.sAMAccountName // empty')
name=$(echo "$input" | jq -r '.name // empty')
mail=$(echo "$input" | jq -r '.mail // empty')

if [[ -z "$sam" ]]; then
    json_error "sAMAccountName is required"
    exit 1
fi

if [[ -z "$name" && -z "$mail" ]]; then
    json_error "At least one field (name or mail) must be provided"
    exit 1
fi

# =========================
# Buscar DN do usuário
# =========================

USER_DN=$(ldapsearch -x -LLL -o ldif-wrap=no \
-H "$LDAP_URI" \
-D "$BIND_DN" -w "$BIND_PW" \
-b "$USERS_OU" \
"(sAMAccountName=$sam)" dn | awk '
/^dn: / {print substr($0,5)}
/^dn:: / {
    cmd="echo " substr($0,6) " | base64 -d"
    cmd | getline decoded
    close(cmd)
    print decoded
}')

if [[ -z "$USER_DN" ]]; then
    json_error "User not found"
    exit 1
fi

# =========================
# Criar arquivo LDIF temporário
# =========================

MOD_FILE=$(mktemp)

{
  echo "dn: $USER_DN"
  echo "changetype: modify"

  if [[ -n "$name" ]]; then
    echo "replace: cn"
    echo "cn: $name"
    echo "-"
    echo "replace: displayName"
    echo "displayName: $name"
    echo "-"
  fi

  if [[ -n "$mail" ]]; then
    echo "replace: mail"
    echo "mail: $mail"
    echo "-"
  fi

} > "$MOD_FILE"

# =========================
# Executar modificação
# =========================

ldapmodify_output=$(ldapmodify -x \
-H "$LDAP_URI" \
-D "$BIND_DN" -w "$BIND_PW" \
-f "$MOD_FILE" 2>&1)

rm -f "$MOD_FILE"

if echo "$ldapmodify_output" | grep -qi "error"; then
    json_error "$ldapmodify_output"
    exit 1
fi

logger -t "nef-api-ad" "USER_EDIT sam=$sam"

json_success "{\"sAMAccountName\":\"$sam\",\"message\":\"User updated successfully\"}"