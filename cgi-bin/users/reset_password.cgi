#!/usr/bin/env bash
set -u

echo "Content-Type: application/json"
echo ""

source "$(dirname "$0")/../lib/common.sh"
validate_ldap_config

input=$(cat)

sam=$(echo "$input" | jq -r '.sAMAccountName // empty')
password=$(echo "$input" | jq -r '.password // empty')

if [[ -z "$sam" || -z "$password" ]]; then
    json_error "sAMAccountName and password are required"
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
# Converter senha para formato AD
# =========================

ENCODED_PWD=$(printf '"%s"' "$password" | iconv -f UTF-8 -t UTF-16LE | base64)

# =========================
# Aplicar redefinição
# =========================

reset_output=$(ldapmodify -x \
-H "$LDAP_URI" \
-D "$BIND_DN" -w "$BIND_PW" <<EOF 2>&1
dn: $USER_DN
changetype: modify
replace: unicodePwd
unicodePwd:: $ENCODED_PWD
-
replace: pwdLastSet
pwdLastSet: 0
EOF
)

if echo "$reset_output" | grep -qi "error"; then
    json_error "$reset_output"
    exit 1
fi

logger -t "nef-api-ad" "USER_RESET_PASSWORD sam=$sam"

json_success "{\"sAMAccountName\":\"$sam\",\"message\":\"Password reset successfully and must change at next logon\"}"