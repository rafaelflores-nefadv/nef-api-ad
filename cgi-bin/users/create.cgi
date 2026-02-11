#!/usr/bin/env bash
set -u

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

# =========================
# Separar Nome / Sobrenome
# =========================

IFS=' ' read -ra NAME_PARTS <<< "$name"
NAME_COUNT=${#NAME_PARTS[@]}

if [[ "$NAME_COUNT" -lt 2 ]]; then
    json_error "Full name must contain at least name and surname"
    exit 1
fi

GIVEN_NAME="${NAME_PARTS[0]}"
SURNAME="${name#${GIVEN_NAME} }"

USER_DN="CN=$name,$USERS_OU"

# =========================
# Verificar se usuário já existe
# =========================

if ldapsearch -x -LLL \
    -H "$LDAP_URI" \
    -D "$BIND_DN" -w "$BIND_PW" \
    -b "$BASE_DN" "(sAMAccountName=$sam)" dn | grep -q "^dn:"; then
    json_error "User already exists"
    exit 1
fi

# =========================
# Criar usuário
# =========================

ldapadd -x \
-H "$LDAP_URI" \
-D "$BIND_DN" -w "$BIND_PW" <<EOF
dn: $USER_DN
objectClass: top
objectClass: person
objectClass: organizationalPerson
objectClass: user
cn: $name
displayName: $name
name: $name
givenName: $GIVEN_NAME
sn: $SURNAME
sAMAccountName: $sam
userPrincipalName: $sam@$(echo "$BASE_DN" | sed 's/DC=//g;s/,/./g')
$( [ -n "$mail" ] && echo "mail: $mail" )
userAccountControl: 544
EOF

# =========================
# Definir senha e ativar
# =========================

ENCODED_PW=$(printf '"%s"' "$password" | iconv -f UTF-8 -t UTF-16LE | base64)

ldapmodify -x \
-H "$LDAP_URI" \
-D "$BIND_DN" -w "$BIND_PW" <<EOF
dn: $USER_DN
changetype: modify
replace: unicodePwd
unicodePwd:: $ENCODED_PW
-
replace: userAccountControl
userAccountControl: 512
-
replace: pwdLastSet
pwdLastSet: 0
EOF

logger -t "nef-api-ad" "USER_CREATE sam=$sam"

json_success "{\"sAMAccountName\":\"$sam\",\"message\":\"User created successfully and must change password at next logon\"}"
