#!/usr/bin/env bash
set -euo pipefail

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
# Localizar DN do usuário
# =========================

USER_DN=$(ldapsearch -x -LLL \
-H "$LDAP_URI" \
-D "$BIND_DN" -w "$BIND_PW" \
-b "$USERS_OU" \
"(sAMAccountName=$sam)" dn | awk '/^dn:/ {print substr($0,5)}')

if [[ -z "$USER_DN" ]]; then
    json_error "User not found"
    exit 1
fi

# =========================
# Montar modificações
# =========================

MOD_FILE=$(mktemp)

echo "dn: $USER_DN" >> "$MOD_FILE"
echo "changetype: modify" >> "$MOD_FILE"

if [[ -n "$name" ]]; then
    echo "replace: cn" >> "$MOD_FILE"
    echo "cn: $name" >> "$MOD_FILE"
    echo "-" >> "$MOD_FILE"

    echo "replace: displayName" >> "$MOD_FILE"
    echo "displayName: $name" >> "$MOD_FILE"
    echo "-" >> "$MOD_FILE"
fi

if [[ -n "$mail" ]]; then
    echo "replace: mail" >> "$MOD_FILE"
    echo "mail: $mail" >> "$MOD_FILE"
    echo "-" >> "$MOD_FILE"
fi

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
