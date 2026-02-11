#!/usr/bin/env bash
set -u
export LANG=en_US.UTF-8

echo "Content-Type: application/json; charset=UTF-8"
echo ""

source "$(dirname "$0")/../lib/common.sh"
validate_ldap_config

input=$(cat)

sam=$(echo "$input" | jq -r '.sAMAccountName // empty')

if [[ -z "$sam" ]]; then
    json_error "sAMAccountName is required"
    exit 1
fi

# =========================
# Buscar DN atual (em qualquer OU)
# =========================

USER_DN=$(ldapsearch -x -LLL -o ldif-wrap=no \
-H "$LDAP_URI" \
-D "$BIND_DN" -w "$BIND_PW" \
-b "$BASE_DN" \
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

CURRENT_CN=$(echo "$USER_DN" | cut -d',' -f1)

# =========================
# 1️⃣ Ativar conta
# =========================

enable_output=$(ldapmodify -x \
-H "$LDAP_URI" \
-D "$BIND_DN" -w "$BIND_PW" <<EOF 2>&1
dn: $USER_DN
changetype: modify
replace: userAccountControl
userAccountControl: 512
EOF
)

if echo "$enable_output" | grep -qi "error"; then
    json_error "$enable_output"
    exit 1
fi

# =========================
# 2️⃣ Mover para OU Usuarios
# =========================

ACTIVE_OU="OU=Usuarios,OU=Nabarrete,DC=nabarrete,DC=local"

move_output=$(ldapmodrdn -x \
-H "$LDAP_URI" \
-D "$BIND_DN" -w "$BIND_PW" \
-r \
-s "$ACTIVE_OU" \
"$USER_DN" \
"$CURRENT_CN" 2>&1)

if echo "$move_output" | grep -qi "error"; then
    json_error "$move_output"
    exit 1
fi

logger -t "nef-api-ad" "USER_ENABLE sam=$sam"

json_success "{\"sAMAccountName\":\"$sam\",\"status\":\"enabled and moved to Usuarios\"}"
