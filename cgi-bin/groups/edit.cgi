#!/usr/bin/env bash
set -euo pipefail

echo "Content-Type: application/json"
echo ""

source "$(dirname "$0")/../lib/common.sh"

validate_ldap_config

# Edit group attributes using ldapmodify
edit_group() {
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
    
    if [[ -z "$description" ]]; then
        json_error "description is required"
        return 1
    fi
    
    # Find DN for group
    local group_dn
    group_dn=$(ldapsearch -H "$LDAP_URI" -D "$BIND_DN" -w "$BIND_PW" \
        -b "$BASE_DN" "(cn=$groupname)" "dn" 2>/dev/null | grep "^dn:" | head -1 | cut -d' ' -f2- || echo "")
    
    if [[ -z "$group_dn" ]]; then
        json_error "Group not found"
        return 1
    fi
    
    # Build LDIF to update description
    local ldif="dn: $group_dn
changetype: modify
replace: description
description: $description"
    
    # Apply changes
    local output
    if output=$(echo "$ldif" | ldapmodify -H "$LDAP_URI" -D "$BIND_DN" -w "$BIND_PW" 2>&1); then
        log_action "GROUP_EDIT" "Group edited: $groupname"
        json_success "{\"groupname\": \"$groupname\", \"message\": \"Group updated successfully\"}"
    else
        json_error "$output"
        return 1
    fi
}

edit_group
