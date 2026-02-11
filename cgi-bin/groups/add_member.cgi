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

    local groupname
    groupname=$(echo "$request" | jq -r '.groupname // empty')

    if [[ -z "$groupname" ]]; then
        json_error "groupname is required"
        return 1
    fi

    local members_json
    members_json=$(echo "$request" | jq -c '.members // empty')

    if [[ -z "$members_json" || "$members_json" == "null" ]]; then
        json_error "members array is required"
        return 1
    fi

    # Escape filtro LDAP
    local safe_group
    safe_group=$(printf '%s' "$groupname" | sed 's/[*()\\]/\\&/g')

    # Buscar DN do grupo (SEM WRAP)
    local group_dn
    group_dn=$(ldapsearch -x -LLL -o ldif-wrap=no \
        -H "$LDAP_URI" \
        -D "$BIND_DN" \
        -w "$BIND_PW" \
        -b "$GROUPS_OU" \
        "(sAMAccountName=$safe_group)" dn | \
        awk '/^dn:/ {print substr($0,5)}')

    if [[ -z "$group_dn" ]]; then
        json_error "Group not found"
        return 1
    fi

    local ldif
    ldif=$(mktemp)

    {
        echo "dn: $group_dn"
        echo "changetype: modify"
        echo "add: member"
    } > "$ldif"

    # Iterar membros sem subshell
    local count
    count=$(echo "$members_json" | jq 'length')

    for ((i=0; i<count; i++)); do

        local member safe_member user_dn
        member=$(echo "$members_json" | jq -r ".[$i]")

        safe_member=$(printf '%s' "$member" | sed 's/[*()\\]/\\&/g')

        user_dn=$(ldapsearch -x -LLL -o ldif-wrap=no \
            -H "$LDAP_URI" \
            -D "$BIND_DN" \
            -w "$BIND_PW" \
            -b "$BASE_DN" \
            "(sAMAccountName=$safe_member)" dn | \
            awk '/^dn:/ {print substr($0,5)}')

        if [[ -z "$user_dn" ]]; then
            rm -f "$ldif"
            json_error "User not found: $member"
            return 1
        fi

        echo "member: $user_dn" >> "$ldif"

    done

    if ldapmodify -x \
        -H "$LDAP_URI" \
        -D "$BIND_DN" \
        -w "$BIND_PW" \
        -f "$ldif" 2>/tmp/ldap_error; then

        log_action "GROUP_ADD_MEMBERS" "Members added to $groupname"
        json_success "{\"groupname\":\"$groupname\",\"members\":$members_json,\"message\":\"Members added successfully\"}"
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