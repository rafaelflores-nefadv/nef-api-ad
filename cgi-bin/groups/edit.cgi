#!/usr/bin/env bash
set -u

echo "Content-Type: application/json"
echo ""

source "$(dirname "$0")/../lib/common.sh"

validate_ldap_config

edit_group() {
    local request
    request=$(parse_json_input)

    local groupname description
    groupname=$(echo "$request" | jq -r '.groupname // empty')
    description=$(echo "$request" | jq -r '.description // empty')

    if [[ -z "$groupname" ]]; then
        json_error "groupname is required"
        return 1
    fi

    if [[ -z "$description" ]]; then
        json_error "description is required"
        return 1
    fi

    # Escape simples para filtro LDAP
    local safe_groupname
    safe_groupname=$(printf '%s' "$groupname" | sed 's/[*()\\]/\\&/g')

    local group_dn
    group_dn=$(ldapsearch -x \
        -H "$LDAP_URI" \
        -D "$BIND_DN" \
        -w "$BIND_PW" \
        -b "$GROUPS_OU" \
        "(sAMAccountName=$safe_groupname)" dn | \
        grep "^dn:" | head -1 | cut -d' ' -f2-)

    if [[ -z "$group_dn" ]]; then
        json_error "Group not found"
        return 1
    fi

    local ldif
    ldif=$(mktemp)

    {
        echo "dn: $group_dn"
        echo "changetype: modify"
        echo "replace: description"
        echo "description: $description"
    } > "$ldif"

    if ldapmodify -x \
        -H "$LDAP_URI" \
        -D "$BIND_DN" \
        -w "$BIND_PW" \
        -f "$ldif" 2>/tmp/ldap_error; then

        log_action "GROUP_EDIT" "Group edited: $groupname"
        json_success "{\"groupname\":\"$groupname\",\"message\":\"Group updated successfully\"}"
    else
        local error
        error=$(cat /tmp/ldap_error)
        json_error "$error"
        rm -f "$ldif"
        return 1
    fi

    rm -f "$ldif"
}

edit_group