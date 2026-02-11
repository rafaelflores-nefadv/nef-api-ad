#!/usr/bin/env bash
set -euo pipefail

echo "Content-Type: application/json"
echo ""

source "$(dirname "$0")/../lib/common.sh"

validate_ldap_config

# Get group by name
get_group() {
    local groupname="$1"
    
    if [[ -z "$groupname" ]]; then
        json_error "group parameter is required"
        return 1
    fi
    
    local filter="(cn=$groupname)"
    local ldap_output
    
    ldap_output=$(ldapsearch -H "$LDAP_URI" -D "$BIND_DN" -w "$BIND_PW" \
        -b "$BASE_DN" "$filter" \
        "cn" "description" "member" 2>/dev/null || echo "")
    
    if [[ -z "$ldap_output" ]]; then
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
            local member="${BASH_REMATCH[1]}"
            # Extract cn from DN
            if [[ "$member" =~ ^cn=([^,]+) ]]; then
                members=$(echo "$members" | jq --arg member "${BASH_REMATCH[1]}" '. += [$member]')
            fi
        fi
    done <<< "$ldap_output"
    
    group_json=$(echo "$group_json" | jq --arg members "$(echo "$members" | jq -c '.')" '.members = ($members|fromjson)')
    json_success "$group_json"
}

groupname=$(get_param "group" || true)
log_action "GROUP_GET" "Getting group $groupname"
get_group "$groupname"
