#!/usr/bin/env bash
set -u
export LANG=en_US.UTF-8

echo "Content-Type: application/json; charset=UTF-8"
echo ""

source "$(dirname "$0")/../lib/common.sh"

validate_ldap_config

login() {
    local request
    request=$(parse_json_input)

    local username password system
    username=$(echo "$request" | jq -r '.username // empty')
    password=$(echo "$request" | jq -r '.password // empty')
    system=$(echo "$request" | jq -r '.system // empty')

    if [[ -z "$username" || -z "$password" || -z "$system" ]]; then
        json_error "Invalid credentials"
        return 1
    fi

    local safe_user safe_system
    safe_user=$(printf '%s' "$username" | sed 's/[*()\\]/\\&/g')
    safe_system=$(printf '%s' "$system" | sed 's/[*()\\]/\\&/g')

    # Buscar DN do usuário
    local user_dn
    user_dn=$(ldapsearch -x -LLL -o ldif-wrap=no \
        -H "$LDAP_URI" \
        -D "$BIND_DN" \
        -w "$BIND_PW" \
        -b "$BASE_DN" \
        "(sAMAccountName=$safe_user)" dn | \
        awk '/^dn:/ {print substr($0,5)}')

    if [[ -z "$user_dn" ]]; then
        json_error "Invalid credentials"
        return 1
    fi

    # Validar senha (bind como usuário)
    if ! ldapsearch -x -LLL -o ldif-wrap=no \
        -H "$LDAP_URI" \
        -D "$user_dn" \
        -w "$password" \
        -b "$BASE_DN" "(objectClass=*)" dn >/dev/null 2>&1; then

        json_error "Invalid credentials"
        return 1
    fi

    # Buscar DN do grupo
    local group_dn
    group_dn=$(ldapsearch -x -LLL -o ldif-wrap=no \
        -H "$LDAP_URI" \
        -D "$BIND_DN" \
        -w "$BIND_PW" \
        -b "$GROUPS_OU" \
        "(sAMAccountName=$safe_system)" dn | \
        awk '/^dn:/ {print substr($0,5)}')

    if [[ -z "$group_dn" ]]; then
        json_error "Invalid credentials"
        return 1
    fi

    # Verificar memberOf no usuário
    local member_check
    member_check=$(ldapsearch -x -LLL -o ldif-wrap=no \
        -H "$LDAP_URI" \
        -D "$BIND_DN" \
        -w "$BIND_PW" \
        -b "$BASE_DN" \
        "(&(sAMAccountName=$safe_user)(memberOf=$group_dn))" dn)

    if ! echo "$member_check" | grep -q "^dn:"; then
        json_error "Invalid credentials"
        return 1
    fi

    json_success "{\"username\":\"$username\",\"system\":\"$system\",\"message\":\"Authentication successful\"}"
}

login