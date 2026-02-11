$baseUrl = "http://192.168.200.8:8025/api/users/edit.cgi"

$body = @{
    sAMAccountName = "teste.api"
    name = "Teste API Alterado PS Novamente"
    mail = "teste.api.ps@nabarrete.local"
}

$json = $body | ConvertTo-Json -Depth 3

Write-Host "`n=== EDIT USER TEST ==="
Write-Host $json

try {
    $response = Invoke-RestMethod `
        -Uri $baseUrl `
        -Method POST `
        -ContentType "application/json" `
        -Body $json

    Write-Host "`nResponse:"
    $response | ConvertTo-Json -Depth 5
}
catch {
    Write-Host "`nERROR:"
    Write-Host $_.Exception.Message
}
