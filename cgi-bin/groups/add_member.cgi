#!/usr/bin/env bash
set -u
export LANG=en_US.UTF-8

echo "Content-Type: application/json; charset=UTF-8"
echo ""

source "$(dirname "$0")/../lib/common.sh"

validate_ldap_config

add_member() {
    local request
    request=$(parse_json_input)

    local groupname member
    groupname=$(echo "$request" | jq -r '.groupname // empty')
    member=$(echo "$request" | jq -r '.member // empty')

    if [[ -z "$groupname" ]]; then
        json_error "groupname is required"
        return 1
    fi

    if [[ -z "$member" ]]; then
        json_error "member is required"
        return 1
    fi

    # Escape filtro LDAP
    local safe_group safe_member
    safe_group=$(printf '%s' "$groupname" | sed 's/[*()\\]/\\&/g')
    safe_member=$(printf '%s' "$member" | sed 's/[*()\\]/\\&/g')

    # Buscar DN do grupo
    local group_dn
    group_dn=$(ldapsearch -x \
        -H "$LDAP_URI" \
        -D "$BIND_DN" \
        -w "$BIND_PW" \
        -b "$GROUPS_OU" \
        "(sAMAccountName=$safe_group)" dn | \
        grep "^dn:" | head -1 | cut -d' ' -f2-)

    if [[ -z "$group_dn" ]]; then
        json_error "Group not found"
        return 1
    fi

    # Buscar DN do usuário
    local user_dn
    user_dn=$(ldapsearch -x \
        -H "$LDAP_URI" \
        -D "$BIND_DN" \
        -w "$BIND_PW" \
        -b "$BASE_DN" \
        "(sAMAccountName=$safe_member)" dn | \
        grep "^dn:" | head -1 | cut -d' ' -f2-)

    if [[ -z "$user_dn" ]]; then
        json_error "User not found"
        return 1
    fi

    local ldif
    ldif=$(mktemp)

    {
        echo "dn: $group_dn"
        echo "changetype: modify"
        echo "add: member"
        echo "member: $user_dn"
    } > "$ldif"

    if ldapmodify -x \
        -H "$LDAP_URI" \
        -D "$BIND_DN" \
        -w "$BIND_PW" \
        -f "$ldif" 2>/tmp/ldap_error; then

        log_action "GROUP_ADD_MEMBER" "Member $member added to $groupname"
        json_success "{\"groupname\":\"$groupname\",\"member\":\"$member\",\"message\":\"Member added successfully\"}"
    else
        local error
        error=$(cat /tmp/ldap_error)
        json_error "$error"
        rm -f "$ldif"
        return 1
    fi

    rm -f "$ldif"
}

add_member