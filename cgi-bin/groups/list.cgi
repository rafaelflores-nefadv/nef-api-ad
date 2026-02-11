#!/usr/bin/env bash
set -euo pipefail

echo "Content-Type: application/json"
echo ""

source "$(dirname "$0")/../lib/common.sh"

validate_ldap_config

list_groups() {
    local filter="(objectClass=group)"
    local ldap_output
    
    ldap_output=$(ldapsearch -LLL -H "$LDAP_URI" \
        -D "$BIND_DN" -w "$BIND_PW" \
        -b "$BASE_DN" "$filter" \
        "cn" "description" "member" 2>/dev/null || echo "")
    
    if [[ -z "$ldap_output" ]]; then
        json_success '[]'
        return 0
    fi
    
    local groups="[]"
    local current_dn=""
    local current_cn=""
    local current_desc=""
    local member_count=0
    
    while IFS= read -r line; do
        
        if [[ "$line" =~ ^dn:\ (.+) ]]; then
            # salva grupo anterior
            if [[ -n "$current_dn" && -n "$current_cn" ]]; then
                groups=$(echo "$groups" | jq \
                    --arg cn "$current_cn" \
                    --arg desc "$current_desc" \
                    --argjson count "$member_count" \
                    '. += [{"cn": $cn, "description": $desc, "memberCount": $count}]')
            fi
            
            current_dn="${BASH_REMATCH[1]}"
            current_cn=""
            current_desc=""
            member_count=0
        
        elif [[ "$line" =~ ^cn:\ (.+) ]]; then
            current_cn="${BASH_REMATCH[1]}"
        
        elif [[ "$line" =~ ^description:\ (.+) ]]; then
            current_desc="${BASH_REMATCH[1]}"
        
        elif [[ "$line" =~ ^member:\ (.+) ]]; then
            (( member_count++ ))
        fi
    
    done <<< "$ldap_output"
    
    # salva último grupo
    if [[ -n "$current_dn" && -n "$current_cn" ]]; then
        groups=$(echo "$groups" | jq \
            --arg cn "$current_cn" \
            --arg desc "$current_desc" \
            --argjson count "$member_count" \
            '. += [{"cn": $cn, "description": $desc, "memberCount": $count}]')
    fi

    # ordenação alfabética
    groups=$(echo "$groups" | jq 'sort_by(.cn | ascii_downcase)')
    
    json_success "$groups"
}

log_action "GROUP_LIST" "Listing groups"
list_groups