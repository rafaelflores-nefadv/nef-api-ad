$baseUrl = "http://192.168.200.8:8025/api/users/set_groups.cgi"

$body = @{
    sAMAccountName = "teste.api"
    groups = @(
        "administrativo",
        "sicredi_biomas"
    )
}

$json = $body | ConvertTo-Json -Depth 5

Write-Host "`n=== SET GROUPS TEST ==="
Write-Host $json

$response = Invoke-RestMethod `
    -Uri $baseUrl `
    -Method POST `
    -ContentType "application/json" `
    -Body $json

$response | ConvertTo-Json -Depth 6