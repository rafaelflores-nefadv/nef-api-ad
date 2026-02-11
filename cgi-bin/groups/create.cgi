#!/usr/bin/env bash
set -euo pipefail

echo "Content-Type: application/json"
echo ""

source "$(dirname "$0")/../lib/common.sh"

validate_ldap_config

# Create a new group using samba-tool
create_group() {
    local request
    request=$(parse_json_input)
    
    # Extract fields from JSON
    local groupname description
    
    groupname=$(echo "$request" | jq -r '.groupname // empty' 2>/dev/null || echo "")
    description=$(echo "$request" | jq -r '.description // empty' 2>/dev/null || echo "")
    
    if [[ -z "$groupname" ]]; then
        json_error "groupname is required"
        return 1
    fi
    
    local samba_cmd="samba-tool group add '$groupname'"
    
    if [[ -n "$description" ]]; then
        samba_cmd="$samba_cmd --description='$description'"
    fi
    
    local output
    if output=$(eval "$samba_cmd" 2>&1); then
        log_action "GROUP_CREATE" "Group created: $groupname"
        json_success "{\"groupname\": \"$groupname\", \"message\": \"Group created successfully\"}"
    else
        json_error "$output"
        return 1
    fi
}

create_group
