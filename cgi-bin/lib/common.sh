#!/usr/bin/env bash

# Import environment variables safely
LDAP_URI="${LDAP_URI:-}"
BIND_DN="${BIND_DN:-}"
BIND_PW="${BIND_PW:-}"
BASE_DN="${BASE_DN:-}"
USERS_OU="${USERS_OU:-}"

set -euo pipefail

# Output JSON success response
json_success() {
    local data="${1:-null}"
    echo "{\"success\": true, \"data\": $data, \"error\": null}"
}

# Output JSON error response
json_error() {
    local error_msg="$1"
    echo "{\"success\": false, \"data\": null, \"error\": \"$error_msg\"}"
}

# Check if required environment variables are set
require_env() {
    local var_name="$1"
    if [[ -z "${!var_name:-}" ]]; then
        json_error "Environment variable $var_name is not set"
        exit 1
    fi
}

# Parse JSON input from stdin
parse_json_input() {
    local json_input
    json_input=$(cat)
    echo "$json_input"
}

# Log action to syslog
log_action() {
    local action="$1"
    local details="${2:-}"
    logger -t "nef-api-ad" "$action: $details"
}

# Get query parameter from QUERY_STRING
get_param() {
    local param="$1"
    local qs="${QUERY_STRING:-}"
    
    if [[ -z "$qs" ]]; then
        return 1
    fi
    
    # Parse query string for parameter
    if [[ "$qs" =~ (^|&)${param}=([^&]+) ]]; then
        echo "${BASH_REMATCH[2]}" | sed 's/%20/ /g; s/%21/!/g; s/%40/@/g'
        return 0
    fi
    return 1
}

# Escape string for LDIF format
escape_ldif() {
    local str="$1"
    echo "$str" | sed 's/\\/\\\\/g'
}

# Validate required LDAP environment variables
validate_ldap_config() {
    for var in LDAP_URI BIND_DN BIND_PW BASE_DN USERS_OU; do
        if [[ -z "${!var:-}" ]]; then
            json_error "Environment variable $var is not set"
            exit 1
        fi
    done
}

# Validação de API Key
validate_api_key() {
    if [[ -z "${HTTP_X_API_KEY:-}" ]]; then
        echo '{"success":false,"data":null,"error":"Unauthorized"}'
        exit 1
    fi

    if [[ "$HTTP_X_API_KEY" != "$API_KEY" ]]; then
        echo '{"success":false,"data":null,"error":"Unauthorized"}'
        exit 1
    fi
}
