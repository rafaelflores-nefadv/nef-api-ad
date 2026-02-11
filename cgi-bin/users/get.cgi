#!/usr/bin/env bash
set -euo pipefail

echo "Content-Type: application/json"
echo ""

source "$(dirname "$0")/../lib/common.sh"

validate_ldap_config

# Get user by username
get_user() {
    local username="$1"
    
    if [[ -z "$username" ]]; then
        json_error "username parameter is required"
        return 1
    fi
    
    local filter="(cn=$username)"
    local ldap_output
    
    ldap_output=$(ldapsearch -H "$LDAP_URI" -D "$BIND_DN" -w "$BIND_PW" \
        -b "ou=$USERS_OU,$BASE_DN" "$filter" \
        "cn" "mail" "userAccountControl" "sn" "givenName" "description" 2>/dev/null || echo "")
    
    if [[ -z "$ldap_output" ]]; then
        json_error "User not found"
        return 1
    fi
    
    local user_json="{}"
    local status="disabled"
    
    while IFS= read -r line; do
        if [[ "$line" =~ ^cn:\ (.+) ]]; then
            user_json=$(echo "$user_json" | jq --arg val "${BASH_REMATCH[1]}" '.cn = $val')
        elif [[ "$line" =~ ^mail:\ (.+) ]]; then
            user_json=$(echo "$user_json" | jq --arg val "${BASH_REMATCH[1]}" '.mail = $val')
        elif [[ "$line" =~ ^sn:\ (.+) ]]; then
            user_json=$(echo "$user_json" | jq --arg val "${BASH_REMATCH[1]}" '.sn = $val')
        elif [[ "$line" =~ ^givenName:\ (.+) ]]; then
            user_json=$(echo "$user_json" | jq --arg val "${BASH_REMATCH[1]}" '.givenName = $val')
        elif [[ "$line" =~ ^description:\ (.+) ]]; then
            user_json=$(echo "$user_json" | jq --arg val "${BASH_REMATCH[1]}" '.description = $val')
        elif [[ "$line" =~ ^userAccountControl:\ (.+) ]]; then
            local uac="${BASH_REMATCH[1]}"
            if (( uac & 2 )); then
                status="disabled"
            else
                status="enabled"
            fi
        fi
    done <<< "$ldap_output"
    
    user_json=$(echo "$user_json" | jq --arg val "$status" '.status = $val')
    json_success "$user_json"
}

username=$(get_param "username" || true)
log_action "USER_GET" "Getting user $username"
get_user "$username"
