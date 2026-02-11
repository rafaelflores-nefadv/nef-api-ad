#!/usr/bin/env bash
set -euo pipefail

echo "Content-Type: application/json"
echo ""

source "$(dirname "$0")/../lib/common.sh"

validate_ldap_config

# Create a new user using samba-tool
create_user() {
    local request
    request=$(parse_json_input)
    
    # Extract fields from JSON
    local username givenName sn mail password
    
    username=$(echo "$request" | jq -r '.username // empty' 2>/dev/null || echo "")
    givenName=$(echo "$request" | jq -r '.givenName // empty' 2>/dev/null || echo "")
    sn=$(echo "$request" | jq -r '.sn // empty' 2>/dev/null || echo "")
    mail=$(echo "$request" | jq -r '.mail // empty' 2>/dev/null || echo "")
    password=$(echo "$request" | jq -r '.password // empty' 2>/dev/null || echo "")
    
    if [[ -z "$username" || -z "$password" ]]; then
        json_error "username and password are required"
        return 1
    fi
    
    local samba_cmd="samba-tool user create $username $password"
    
    if [[ -n "$givenName" ]]; then
        samba_cmd="$samba_cmd --given-name='$givenName'"
    fi
    
    if [[ -n "$sn" ]]; then
        samba_cmd="$samba_cmd --surname='$sn'"
    fi
    
    if [[ -n "$mail" ]]; then
        samba_cmd="$samba_cmd --mail-address='$mail'"
    fi
    
    local output
    if output=$(eval "$samba_cmd" 2>&1); then
        log_action "USER_CREATE" "User created: $username"
        json_success "{\"username\": \"$username\", \"message\": \"User created successfully\"}"
    else
        json_error "$output"
        return 1
    fi
}

create_user
