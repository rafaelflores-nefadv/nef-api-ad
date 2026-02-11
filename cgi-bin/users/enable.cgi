#!/usr/bin/env bash
set -euo pipefail

echo "Content-Type: application/json"
echo ""

source "$(dirname "$0")/../lib/common.sh"

validate_ldap_config

# Enable user account (remove DISABLED flag)
enable_user() {
    local request
    request=$(parse_json_input)
    
    local username
    username=$(echo "$request" | jq -r '.username // empty' 2>/dev/null || echo "")
    
    if [[ -z "$username" ]]; then
        json_error "username is required"
        return 1
    fi
    
    local output
    if output=$(samba-tool user enable "$username" 2>&1); then
        log_action "USER_ENABLE" "User enabled: $username"
        json_success "{\"username\": \"$username\", \"status\": \"enabled\"}"
    else
        json_error "$output"
        return 1
    fi
}

enable_user
