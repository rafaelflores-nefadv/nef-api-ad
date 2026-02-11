$baseUrl = "http://192.168.200.8:8025/api/users/disable.cgi"

function Test-DisableUser {
    param(
        [Parameter(Mandatory=$true)]
        [string]$SamAccountName
    )

    $body = @{
        sAMAccountName = $SamAccountName
    }

    $json = $body | ConvertTo-Json -Depth 3

    Write-Host "`n=== DISABLE USER TEST ==="
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
# EXECUTAR TESTE
# ================================

Test-DisableUser -SamAccountName "teste.api"
