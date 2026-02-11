#!/usr/bin/env bash
set -u

echo "Content-Type: application/json"
echo ""

source "$(dirname "$0")/../lib/common.sh"
validate_ldap_config

input=$(cat)

sam=$(echo "$input" | jq -r '.sAMAccountName // empty')
groups=$(echo "$input" | jq -r '.groups[]?' 2>/dev/null)

if [[ -z "$sam" ]]; then
    json_error "sAMAccountName is required"
    exit 1
fi

# =========================
# Buscar DN do usuário
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

# =========================
# Remover de todos os grupos atuais
# =========================

CURRENT_GROUPS=$(ldapsearch -x -LLL -o ldif-wrap=no \
-H "$LDAP_URI" \
-D "$BIND_DN" -w "$BIND_PW" \
-b "$BASE_DN" \
"(sAMAccountName=$sam)" memberOf | awk '/^memberOf: / {print substr($0,11)}')

for group_dn in $CURRENT_GROUPS; do
    ldapmodify -x \
    -H "$LDAP_URI" \
    -D "$BIND_DN" -w "$BIND_PW" <<EOF >/dev/null 2>&1
dn: $group_dn
changetype: modify
delete: member
member: $USER_DN
EOF
done

# =========================
# Adicionar aos grupos recebidos
# =========================

for group in $groups; do

    GROUP_DN=$(ldapsearch -x -LLL -o ldif-wrap=no \
    -H "$LDAP_URI" \
    -D "$BIND_DN" -w "$BIND_PW" \
    -b "$BASE_DN" \
    "(cn=$group)" dn | awk '/^dn: / {print substr($0,5)}')

    if [[ -n "$GROUP_DN" ]]; then
        ldapmodify -x \
        -H "$LDAP_URI" \
        -D "$BIND_DN" -w "$BIND_PW" <<EOF >/dev/null 2>&1
dn: $GROUP_DN
changetype: modify
add: member
member: $USER_DN
EOF
    fi

done

logger -t "nef-api-ad" "USER_SET_GROUPS sam=$sam"

json_success "{\"sAMAccountName\":\"$sam\",\"message\":\"Groups synchronized successfully\"}"