#!/usr/bin/env bash
set -u

echo "Content-Type: application/json"
echo ""

source "$(dirname "$0")/../lib/common.sh"
validate_ldap_config

# =========================
# Obter parâmetro
# =========================

sam=$(get_param "sAMAccountName" || true)

if [[ -z "$sam" ]]; then
    json_error "sAMAccountName parameter is required"
    exit 1
fi

# =========================
# Buscar usuário
# =========================

ldap_output=$(ldapsearch -x -LLL -o ldif-wrap=no \
-H "$LDAP_URI" \
-D "$BIND_DN" -w "$BIND_PW" \
-b "$BASE_DN" \
"(sAMAccountName=$sam)" \
displayName givenName sn mail sAMAccountName userAccountControl memberOf 2>/dev/null)

if [[ -z "$ldap_output" ]]; then
    json_error "User not found"
    exit 1
fi

displayName=""
givenName=""
sn=""
mail=""
status="enabled"
groups=()

while IFS= read -r line; do

    case "$line" in
        displayName:\ *)
            displayName="${line#displayName: }"
            ;;
        givenName:\ *)
            givenName="${line#givenName: }"
            ;;
        sn:\ *)
            sn="${line#sn: }"
            ;;
        mail:\ *)
            mail="${line#mail: }"
            ;;
        userAccountControl:\ *)
            uac="${line#userAccountControl: }"
            if (( uac & 2 )); then
                status="disabled"
            else
                status="enabled"
            fi
            ;;
        memberOf:\ *)
            group_dn="${line#memberOf: }"
            group_name=$(echo "$group_dn" | cut -d',' -f1 | sed 's/^CN=//')
            groups+=("\"$group_name\"")
            ;;
    esac

done <<< "$ldap_output"

groups_json="[$(IFS=,; echo "${groups[*]}")]"

# =========================
# Montar JSON final
# =========================

user_json=$(jq -n \
    --arg displayName "$displayName" \
    --arg givenName "$givenName" \
    --arg sn "$sn" \
    --arg mail "$mail" \
    --arg sam "$sam" \
    --arg status "$status" \
    --argjson groups "$groups_json" \
    '{
        sAMAccountName: $sam,
        displayName: $displayName,
        givenName: $givenName,
        sn: $sn,
        mail: $mail,
        status: $status,
        groups: $groups
    }')

log_action "USER_GET" "User retrieved: $sam"

json_success "$user_json"