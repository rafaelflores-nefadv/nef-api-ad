# ===============================
# CONFIG
# ===============================

$Url = "http://192.168.200.8:8025/api/groups/add_member.cgi"

$Body = @{
    groupname = "GRP_TESTE_API"
    members   = @(
        "rafael.flores"
    )
} | ConvertTo-Json -Depth 5

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
    $Response | ConvertTo-Json -Depth 10
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
