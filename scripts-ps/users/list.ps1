$Url = "http://192.168.200.8:8025/api/users/list.cgi"

Invoke-RestMethod `
  -Uri $Url `
  -Method GET `
  -Headers @{ "X-API-KEY" = "1750a0ae9397834b39fa41ccea749949451d84c098b5e017d1ab55f4cb312c9b" }
