$baseUrl = "http://192.168.200.8:8025/api/users/create.cgi"

function Test-CreateUser {
    param(
        [string]$Name,
        [string]$SamAccountName,
        [string]$Password,
        [string]$Mail = $null
    )

    $body = @{
        name = $Name
        sAMAccountName = $SamAccountName
        password = $Password
    }

    if ($Mail) {
        $body.mail = $Mail
    }

    $json = $body | ConvertTo-Json -Depth 3

    Write-Host "`n=== CREATE USER TEST ==="
    Write-Host "Request:"
    Write-Host $json
    Write-Host ""

    try {
        $response = Invoke-RestMethod `
            -Uri $baseUrl `
            -Method POST `
            -ContentType "application/json" `
            -Body $json

        Write-Host "Response:"
        $response | ConvertTo-Json -Depth 5
    }
    catch {
        Write-Host "ERROR:"
        Write-Host $_.Exception.Message
    }
}

# ================================
# Executar teste
# ================================

Test-CreateUser `
    -Name "Teste API Silva" `
    -SamAccountName "teste.api" `
    -Password "Nabarrete@123" `
    -Mail "teste.api@nabarrete.local"