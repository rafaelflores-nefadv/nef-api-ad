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

# =====================================
# Função segura para buscar DN
# =====================================

get_dn() {
    ldapsearch -x -LLL -o ldif-wrap=no \
        -H "$LDAP_URI" \
        -D "$BIND_DN" -w "$BIND_PW" \
        -b "$BASE_DN" \
        "(sAMAccountName=$1)" dn | \
    while IFS= read -r line; do
        case "$line" in
            dn:\ *)
                echo "${line#dn: }"
                ;;
            dn::\ *)
                printf '%s' "${line#dn:: }" | base64 -d
                ;;
        esac
    done
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

# =====================================
# Remover target de todos os grupos atuais
# =====================================

ldapsearch -x -LLL -o ldif-wrap=no \
    -H "$LDAP_URI" \
    -D "$BIND_DN" -w "$BIND_PW" \
    -b "$TARGET_DN" "(objectClass=user)" memberOf | \
while IFS= read -r line; do

    case "$line" in
        memberOf:\ *)
            GROUP_DN="${line#memberOf: }"
            ;;
        memberOf::\ *)
            GROUP_DN=$(printf '%s' "${line#memberOf:: }" | base64 -d)
            ;;
        *)
            continue
            ;;
    esac

    ldapmodify -x \
        -H "$LDAP_URI" \
        -D "$BIND_DN" -w "$BIND_PW" <<EOF >/dev/null 2>&1
dn: $GROUP_DN
changetype: modify
delete: member
member: $TARGET_DN
EOF

done

# =====================================
# Copiar grupos do source para target
# =====================================

ldapsearch -x -LLL -o ldif-wrap=no \
    -H "$LDAP_URI" \
    -D "$BIND_DN" -w "$BIND_PW" \
    -b "$SOURCE_DN" "(objectClass=user)" memberOf | \
while IFS= read -r line; do

    case "$line" in
        memberOf:\ *)
            GROUP_DN="${line#memberOf: }"
            ;;
        memberOf::\ *)
            GROUP_DN=$(printf '%s' "${line#memberOf:: }" | base64 -d)
            ;;
        *)
            continue
            ;;
    esac

    ldapmodify -x \
        -H "$LDAP_URI" \
        -D "$BIND_DN" -w "$BIND_PW" <<EOF >/dev/null 2>&1
dn: $GROUP_DN
changetype: modify
add: member
member: $TARGET_DN
EOF

done

logger -t "nef-api-ad" "USER_COPY_GROUPS from=$source_sam to=$target_sam"

json_success "{\"source\":\"$source_sam\",\"target\":\"$target_sam\",\"message\":\"Groups copied successfully\"}"