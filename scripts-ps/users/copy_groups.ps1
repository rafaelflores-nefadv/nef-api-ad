$baseUrl = "http://192.168.200.8:8025/api/users/copy_groups.cgi"

$body = @{
    sourceSamAccountName = "thaily.goncalves"
    targetSamAccountName = "teste.api"
}

$json = $body | ConvertTo-Json -Depth 3

Write-Host "`n=== COPY GROUPS TEST ==="
Write-Host $json

$response = Invoke-RestMethod `
    -Uri $baseUrl `
    -Method POST `
    -ContentType "application/json" `
    -Body $json

$response | ConvertTo-Json -Depth 6