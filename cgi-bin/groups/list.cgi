#!/usr/bin/env bash
set -euo pipefail

echo "Content-Type: application/json"
echo ""

source "$(dirname "$0")/../lib/common.sh"
validate_ldap_config

# GROUPS_OU já contém o DN completo (não concatenar com BASE_DN)
BASE_GROUP_DN="$GROUPS_OU"

ldap_output=$(ldapsearch -LLL -H "$LDAP_URI" \
-D "$BIND_DN" -w "$BIND_PW" \
-b "$BASE_GROUP_DN" \
"(objectCategory=group)" \
cn description member 2>/dev/null || true)

if [[ -z "$ldap_output" ]]; then
    json_success '[]'
    exit 0
fi

groups=$(echo "$ldap_output" | awk '
BEGIN {
    print "["
    first=1
}
/^dn:/ {
    if (cn != "") {
        if (!first) printf ","
        printf "{\"cn\":\"%s\",\"description\":\"%s\",\"memberCount\":%d}", cn, desc, count
        first=0
    }
    cn=""; desc=""; count=0
}
/^cn:: / {
    sub(/^cn:: /, "")
    cmd = "echo " $0 " | base64 -d"
    cmd | getline cn
    close(cmd)
}
/^cn: / {
    sub(/^cn: /, "")
    cn=$0
}
/^description:/ {
    sub(/^description: /, "")
    desc=$0
}
/^member:/ {
    count++
}
END {
    if (cn != "") {
        if (!first) printf ","
        printf "{\"cn\":\"%s\",\"description\":\"%s\",\"memberCount\":%d}", cn, desc, count
    }
    print "]"
}')

json_success "$groups"