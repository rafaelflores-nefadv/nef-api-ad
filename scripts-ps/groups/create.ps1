# ===============================
# CONFIG
# ===============================

$Url = "http://192.168.200.8:8025/api/groups/create.cgi"

$Body = @{
    groupname  = "GRP_TESTE_API"
    description = "Grupo criado via API NEF"
} | ConvertTo-Json -Depth 3

# ===============================
# REQUEST
# ===============================

try {
    $Response = Invoke-RestMethod `
        -Uri $Url `
        -Method POST `
        -ContentType "application/json" `
        -Body $Body

    Write-Host "===== SUCESSO =====" -ForegroundColor Green
    $Response | ConvertTo-Json -Depth 5
}
catch {
    Write-Host "===== ERRO =====" -ForegroundColor Red
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $responseBody = $reader.ReadToEnd()
        Write-Host $responseBody
    } else {
        Write-Host $_.Exception.Message
    }
}