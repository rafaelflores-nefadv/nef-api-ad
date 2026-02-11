#!/usr/bin/env bash
set -euo pipefail

echo "Content-Type: application/json"
echo ""

source "$(dirname "$0")/../lib/common.sh"

validate_ldap_config

# Add member to group
add_member() {
    local request
    request=$(parse_json_input)
    
    # Extract fields from JSON
    local groupname member
    
    groupname=$(echo "$request" | jq -r '.groupname // empty' 2>/dev/null || echo "")
    member=$(echo "$request" | jq -r '.member // empty' 2>/dev/null || echo "")
    
    if [[ -z "$groupname" ]]; then
        json_error "groupname is required"
        return 1
    fi
    
    if [[ -z "$member" ]]; then
        json_error "member is required"
        return 1
    fi
    
    local output
    if output=$(samba-tool group addmembers "$groupname" "$member" 2>&1); then
        log_action "GROUP_ADD_MEMBER" "Member $member added to $groupname"
        json_success "{\"groupname\": \"$groupname\", \"member\": \"$member\", \"message\": \"Member added successfully\"}"
    else
        json_error "$output"
        return 1
    fi
}

add_member
