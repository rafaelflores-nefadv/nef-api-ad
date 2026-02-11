#!/usr/bin/env bash
set -euo pipefail

echo "Content-Type: application/json; charset=UTF-8"
echo ""

source "$(dirname "$0")/../lib/common.sh"

validate_ldap_config

# Remove member from group
remove_member() {
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
    if output=$(samba-tool group removemembers "$groupname" "$member" 2>&1); then
        log_action "GROUP_REMOVE_MEMBER" "Member $member removed from $groupname"
        json_success "{\"groupname\": \"$groupname\", \"member\": \"$member\", \"message\": \"Member removed successfully\"}"
    else
        json_error "$output"
        return 1
    fi
}

remove_member
