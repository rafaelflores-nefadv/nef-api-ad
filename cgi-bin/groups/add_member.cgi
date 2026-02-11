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

    # Aceita array obrigatório
    local members_json
    members_json=$(echo "$request" | jq -c '.members // empty')

    if [[ -z "$members_json" || "$members_json" == "null" ]]; then
        json_error "members array is required"
        return 1
    fi

    # Escape filtro
    local safe_group
    safe_group=$(printf '%s' "$groupname" | sed 's/[*()\\]/\\&/g')

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

    local ldif
    ldif=$(mktemp)

    echo "dn: $group_dn" > "$ldif"
    echo "changetype: modify" >> "$ldif"
    echo "add: member" >> "$ldif"

    # Iterar membros
    echo "$members_json" | jq -r '.[]' | while read -r member; do

        safe_member=$(printf '%s' "$member" | sed 's/[*()\\]/\\&/g')

        user_dn=$(ldapsearch -x \
            -H "$LDAP_URI" \
            -D "$BIND_DN" \
            -w "$BIND_PW" \
            -b "$USERS_OU" \
            "(sAMAccountName=$safe_member)" dn | \
            grep "^dn:" | head -1 | cut -d' ' -f2-)

        if [[ -z "$user_dn" ]]; then
            rm -f "$ldif"
            json_error "User not found: $member"
            exit 1
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
        error=$(cat /tmp/ldap_error)
        json_error "$error"
        rm -f "$ldif"
        return 1
    fi

    rm -f "$ldif"
}

add_member