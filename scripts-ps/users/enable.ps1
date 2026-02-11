$baseUrl = "http://192.168.200.8:8025/api/users/enable.cgi"

$body = @{
    sAMAccountName = "teste.api"
}

$json = $body | ConvertTo-Json -Depth 3

Write-Host "`n=== ENABLE USER TEST ==="
Write-Host $json

$response = Invoke-RestMethod `
    -Uri $baseUrl `
    -Method POST `
    -ContentType "application/json" `
    -Body $json

$response | ConvertTo-Json -Depth 5