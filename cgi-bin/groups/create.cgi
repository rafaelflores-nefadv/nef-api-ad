#!/usr/bin/env bash
set -u

echo "Content-Type: application/json"
echo ""

source "$(dirname "$0")/../lib/common.sh"

validate_ldap_config

create_group() {
    local request
    request=$(parse_json_input)

    local groupname description
    groupname=$(echo "$request" | jq -r '.groupname // empty')
    description=$(echo "$request" | jq -r '.description // empty')

    if [[ -z "$groupname" ]]; then
        json_error "groupname is required"
        return 1
    fi

    local base_dn="OU=Grupos,OU=Nabarrete,$LDAP_BASE_DN"
    local group_dn="CN=$groupname,$base_dn"

    local ldif
    ldif=$(mktemp)

    {
        echo "dn: $group_dn"
        echo "objectClass: top"
        echo "objectClass: group"
        echo "cn: $groupname"
        echo "sAMAccountName: $groupname"
        echo "groupType: -2147483646"
        if [[ -n "$description" ]]; then
            echo "description: $description"
        fi
    } > "$ldif"

    if ldapadd -x \
        -D "$LDAP_ADMIN_DN" \
        -w "$LDAP_ADMIN_PASSWORD" \
        -H "$LDAP_URI" \
        -f "$ldif" 2>/tmp/ldap_error; then

        log_action "GROUP_CREATE" "Group created: $groupname"
        json_success "{\"groupname\":\"$groupname\",\"message\":\"Group created successfully\"}"
    else
        local error
        error=$(cat /tmp/ldap_error)
        json_error "$error"
        rm -f "$ldif"
        return 1
    fi

    rm -f "$ldif"
}

create_group