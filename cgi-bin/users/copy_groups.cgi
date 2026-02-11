#!/usr/bin/env bash
set -u

echo "Content-Type: application/json"
echo ""

source "$(dirname "$0")/../lib/common.sh"
validate_ldap_config

input=$(cat)

source_sam=$(echo "$input" | jq -r '.sourceSamAccountName // empty')
target_sam=$(echo "$input" | jq -r '.targetSamAccountName // empty')

if [[ -z "$source_sam" || -z "$target_sam" ]]; then
    json_error "sourceSamAccountName and targetSamAccountName are required"
    exit 1
fi

# =========================
# Buscar DN dos usuários
# =========================

get_dn() {
    ldapsearch -x -LLL -o ldif-wrap=no \
    -H "$LDAP_URI" \
    -D "$BIND_DN" -w "$BIND_PW" \
    -b "$BASE_DN" \
    "(sAMAccountName=$1)" dn | awk '
    /^dn: / {print substr($0,5)}
    /^dn:: / {
        cmd="echo " substr($0,6) " | base64 -d"
        cmd | getline decoded
        close(cmd)
        print decoded
    }'
}

SOURCE_DN=$(get_dn "$source_sam")
TARGET_DN=$(get_dn "$target_sam")

if [[ -z "$SOURCE_DN" ]]; then
    json_error "Source user not found"
    exit 1
fi

if [[ -z "$TARGET_DN" ]]; then
    json_error "Target user not found"
    exit 1
fi

# =========================
# Remover target de todos grupos atuais
# =========================

ldapsearch -x -LLL -o ldif-wrap=no \
-H "$LDAP_URI" \
-D "$BIND_DN" -w "$BIND_PW" \
-b "$BASE_DN" \
"(sAMAccountName=$target_sam)" memberOf | \
awk '/^memberOf: / {print substr($0,11)}' | \
while IFS= read -r group_dn; do

    ldapmodify -x \
    -H "$LDAP_URI" \
    -D "$BIND_DN" -w "$BIND_PW" <<EOF >/dev/null 2>&1
dn: $group_dn
changetype: modify
delete: member
member: $TARGET_DN
EOF

done

# =========================
# Copiar grupos do source
# =========================

ldapsearch -x -LLL -o ldif-wrap=no \
-H "$LDAP_URI" \
-D "$BIND_DN" -w "$BIND_PW" \
-b "$BASE_DN" \
"(sAMAccountName=$source_sam)" memberOf | \
awk '/^memberOf: / {print substr($0,11)}' | \
while IFS= read -r group_dn; do

    ldapmodify -x \
    -H "$LDAP_URI" \
    -D "$BIND_DN" -w "$BIND_PW" <<EOF >/dev/null 2>&1
dn: $group_dn
changetype: modify
add: member
member: $TARGET_DN
EOF

done

logger -t "nef-api-ad" "USER_COPY_GROUPS from=$source_sam to=$target_sam"

json_success "{\"message\":\"Groups copied successfully\",\"source\":\"$source_sam\",\"target\":\"$target_sam\"}"