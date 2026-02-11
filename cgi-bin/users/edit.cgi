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
# Separar nome e sobrenome
# =========================

if [[ -n "$name" ]]; then
    firstName=$(echo "$name" | awk '{print $1}')
    lastName=$(echo "$name" | cut -d' ' -f2-)

    if [[ -z "$lastName" ]]; then
        lastName="$firstName"
    fi
fi

# =========================
# Aplicar alterações
# =========================

ldapmodify_output=$(ldapmodify -x \
-H "$LDAP_URI" \
-D "$BIND_DN" -w "$BIND_PW" <<EOF 2>&1
dn: $USER_DN
changetype: modify
$( [[ -n "$name" ]] && echo -e "replace: displayName\ndisplayName: $name\n-" )
$( [[ -n "$name" ]] && echo -e "replace: givenName\ngivenName: $firstName\n-" )
$( [[ -n "$name" ]] && echo -e "replace: sn\nsn: $lastName\n-" )
$( [[ -n "$mail" ]] && echo -e "replace: mail\nmail: $mail\n-" )
EOF
)

if echo "$ldapmodify_output" | grep -qi "error"; then
    json_error "$ldapmodify_output"
    exit 1
fi

logger -t "nef-api-ad" "USER_EDIT sam=$sam"

json_success "{\"sAMAccountName\":\"$sam\",\"message\":\"User updated successfully\"}"