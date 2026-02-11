#!/usr/bin/env bash
set -euo pipefail

echo "Content-Type: application/json"
echo ""

source "$(dirname "$0")/../lib/common.sh"
validate_ldap_config

input=$(cat)

name=$(echo "$input" | jq -r '.name // empty')
sam=$(echo "$input" | jq -r '.sAMAccountName // empty')
password=$(echo "$input" | jq -r '.password // empty')
mail=$(echo "$input" | jq -r '.mail // empty')

if [[ -z "$name" || -z "$sam" || -z "$password" ]]; then
    json_error "name, sAMAccountName and password are required"
    exit 1
fi

USER_DN="CN=$name,$USERS_OU"
DOMAIN="$(echo "$BASE_DN" | sed 's/DC=//g; s/,DC=/./g')"
UPN="${sam}@${DOMAIN}"

# =========================
# 1️⃣ Criar objeto
# =========================

ldapadd_output=$(ldapadd -x \
-H "$LDAP_URI" \
-D "$BIND_DN" -w "$BIND_PW" <<EOF 2>&1
dn: $USER_DN
objectClass: top
objectClass: person
objectClass: organizationalPerson
objectClass: user
cn: $name
displayName: $name
name: $name
sAMAccountName: $sam
userPrincipalName: $UPN
$( [[ -n "$mail" ]] && echo "mail: $mail" )
userAccountControl: 544
EOF
)

if echo "$ldapadd_output" | grep -qi "error"; then
    json_error "$ldapadd_output"
    exit 1
fi

# =========================
# 2️⃣ Definir senha + ativar + forçar troca
# =========================

ldapmodify_output=$(ldapmodify -x \
-H "$LDAP_URI" \
-D "$BIND_DN" -w "$BIND_PW" <<EOF 2>&1
dn: $USER_DN
changetype: modify
replace: unicodePwd
unicodePwd:: $(printf '"%s"' "$password" | iconv -f UTF-8 -t UTF-16LE | base64)
-
replace: userAccountControl
userAccountControl: 512
-
replace: pwdLastSet
pwdLastSet: 0
EOF
)

if echo "$ldapmodify_output" | grep -qi "error"; then
    json_error "$ldapmodify_output"
    exit 1
fi

logger -t "nef-api-ad" "USER_CREATE sam=$sam"

json_success "{\"sAMAccountName\":\"$sam\",\"message\":\"User created and must change password at first logon\"}"