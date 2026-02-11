$baseUrl = "http://192.168.200.8:8025/api/users/reset_password.cgi"

$body = @{
    sAMAccountName = "teste.api"
    password = "NovaSenhaPadrao@123"
}

$json = $body | ConvertTo-Json -Depth 3

Write-Host "`n=== RESET PASSWORD TEST ==="
Write-Host $json

$response = Invoke-RestMethod `
    -Uri $baseUrl `
    -Method POST `
    -ContentType "application/json" `
    -Body $json

$response | ConvertTo-Json -Depth 5
