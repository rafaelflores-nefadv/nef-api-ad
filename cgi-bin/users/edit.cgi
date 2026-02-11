#!/usr/bin/env bash
set -euo pipefail

echo "Content-Type: application/json"
echo ""

source "$(dirname "$0")/../lib/common.sh"

validate_ldap_config

# Edit user attributes using ldapmodify
edit_user() {
    local request
    request=$(parse_json_input)
    
    # Extract fields from JSON
    local username mail givenName sn description
    
    username=$(echo "$request" | jq -r '.username // empty' 2>/dev/null || echo "")
    mail=$(echo "$request" | jq -r '.mail // empty' 2>/dev/null || echo "")
    givenName=$(echo "$request" | jq -r '.givenName // empty' 2>/dev/null || echo "")
    sn=$(echo "$request" | jq -r '.sn // empty' 2>/dev/null || echo "")
    description=$(echo "$request" | jq -r '.description // empty' 2>/dev/null || echo "")
    
    if [[ -z "$username" ]]; then
        json_error "username is required"
        return 1
    fi
    
    # Find DN for user
    local user_dn
    user_dn=$(ldapsearch -H "$LDAP_URI" -D "$BIND_DN" -w "$BIND_PW" \
        -b "ou=$USERS_OU,$BASE_DN" "(cn=$username)" "dn" 2>/dev/null | grep "^dn:" | head -1 | cut -d' ' -f2- || echo "")
    
    if [[ -z "$user_dn" ]]; then
        json_error "User not found"
        return 1
    fi
    
    # Build LDIF
    local ldif="dn: $user_dn
changetype: modify"
    
    if [[ -n "$mail" ]]; then
        ldif="$ldif
replace: mail
mail: $mail
-"
    fi
    
    if [[ -n "$givenName" ]]; then
        ldif="$ldif
replace: givenName
givenName: $givenName
-"
    fi
    
    if [[ -n "$sn" ]]; then
        ldif="$ldif
replace: sn
sn: $sn
-"
    fi
    
    if [[ -n "$description" ]]; then
        ldif="$ldif
replace: description
description: $description
-"
    fi
    
    # Apply changes
    local output
    if output=$(echo "$ldif" | ldapmodify -H "$LDAP_URI" -D "$BIND_DN" -w "$BIND_PW" 2>&1); then
        log_action "USER_EDIT" "User edited: $username"
        json_success "{\"username\": \"$username\", \"message\": \"User updated successfully\"}"
    else
        json_error "$output"
        return 1
    fi
}

edit_user
