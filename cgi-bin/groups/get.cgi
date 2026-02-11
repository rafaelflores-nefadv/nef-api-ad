#!/usr/bin/env bash
set -u
export LANG=en_US.UTF-8

echo "Content-Type: application/json; charset=UTF-8"
echo ""

source "$(dirname "$0")/../lib/common.sh"

validate_ldap_config

get_group() {
    local groupname="$1"

    if [[ -z "$groupname" ]]; then
        json_error "group parameter is required"
        return 1
    fi

    # Escape básico filtro LDAP
    local safe_groupname
    safe_groupname=$(printf '%s' "$groupname" | sed 's/[*()\\]/\\&/g')

    local ldap_output
    ldap_output=$(ldapsearch -x \
        -H "$LDAP_URI" \
        -D "$BIND_DN" \
        -w "$BIND_PW" \
        -b "$GROUPS_OU" \
        "(sAMAccountName=$safe_groupname)" \
        cn description member)

    if ! echo "$ldap_output" | grep -q "^dn:"; then
        json_error "Group not found"
        return 1
    fi

    local group_json="{}"
    local members="[]"

    while IFS= read -r line; do
        if [[ "$line" =~ ^cn:\ (.+) ]]; then
            group_json=$(echo "$group_json" | jq --arg val "${BASH_REMATCH[1]}" '.cn = $val')

        elif [[ "$line" =~ ^description:\ (.+) ]]; then
            group_json=$(echo "$group_json" | jq --arg val "${BASH_REMATCH[1]}" '.description = $val')

        elif [[ "$line" =~ ^member:\ (.+) ]]; then
            local member_dn="${BASH_REMATCH[1]}"
            if [[ "$member_dn" =~ ^CN=([^,]+) ]]; then
                members=$(echo "$members" | jq --arg m "${BASH_REMATCH[1]}" '. += [$m]')
            fi

        elif [[ "$line" =~ ^member::\ (.+) ]]; then
            local decoded
            decoded=$(echo "${BASH_REMATCH[1]}" | base64 -d 2>/dev/null || echo "")
            if [[ "$decoded" =~ ^CN=([^,]+) ]]; then
                members=$(echo "$members" | jq --arg m "${BASH_REMATCH[1]}" '. += [$m]')
            fi
        fi
    done <<< "$ldap_output"

    group_json=$(echo "$group_json" | jq --argjson members "$members" '.members = $members')

    json_success "$group_json"
}

groupname=$(get_param "group" || true)
log_action "GROUP_GET" "Getting group $groupname"
get_group "$groupname"