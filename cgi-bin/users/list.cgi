#!/usr/bin/env bash
set -euo pipefail

echo "Content-Type: application/json; charset=UTF-8"
echo ""

source "$(dirname "$0")/../lib/common.sh"

validate_ldap_config

list_users() {
    local filter="(&(objectCategory=person)(objectClass=user))"
    local ldap_output
    
    ldap_output=$(ldapsearch -LLL -H "$LDAP_URI" \
        -D "$BIND_DN" -w "$BIND_PW" \
        -b "$USERS_OU" "$filter" \
        "cn" "mail" "userAccountControl" "sAMAccountName" 2>/dev/null || echo "")
    
    if [[ -z "$ldap_output" ]]; then
        json_success '[]'
        return 0
    fi
    
    local users="[]"
    local current_dn=""
    local current_cn=""
    local current_mail=""
    local current_sam=""
    local current_status="disabled"
    
    while IFS= read -r line; do
        if [[ "$line" =~ ^dn:\ (.+) ]]; then
            if [[ -n "$current_dn" && -n "$current_cn" ]]; then
                users=$(echo "$users" | jq \
                    --arg cn "$current_cn" \
                    --arg mail "$current_mail" \
                    --arg sam "$current_sam" \
                    --arg status "$current_status" \
                    '. += [{"cn": $cn, "sAMAccountName": $sam, "mail": $mail, "status": $status}]')
            fi
            current_dn="${BASH_REMATCH[1]}"
            current_cn=""
            current_mail=""
            current_sam=""
            current_status="disabled"
        elif [[ "$line" =~ ^cn:\ (.+) ]]; then
            current_cn="${BASH_REMATCH[1]}"
        elif [[ "$line" =~ ^mail:\ (.+) ]]; then
            current_mail="${BASH_REMATCH[1]}"
        elif [[ "$line" =~ ^sAMAccountName:\ (.+) ]]; then
            current_sam="${BASH_REMATCH[1]}"
        elif [[ "$line" =~ ^userAccountControl:\ (.+) ]]; then
            local uac="${BASH_REMATCH[1]}"
            if (( uac & 2 )); then
                current_status="disabled"
            else
                current_status="enabled"
            fi
        fi
    done <<< "$ldap_output"
    
    # Add last user
    if [[ -n "$current_dn" && -n "$current_cn" ]]; then
        users=$(echo "$users" | jq \
            --arg cn "$current_cn" \
            --arg mail "$current_mail" \
            --arg sam "$current_sam" \
            --arg status "$current_status" \
            '. += [{"cn": $cn, "sAMAccountName": $sam, "mail": $mail, "status": $status}]')
    fi

    # Ordenação alfabética pelo CN
    users=$(echo "$users" | jq 'sort_by(.cn | ascii_downcase)')
    
    json_success "$users"
}

log_action "USER_LIST" "Listing users"
list_users