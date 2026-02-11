# ===============================
# CONFIG
# ===============================

$Url = "http://192.168.200.8:8025/api/login/login.cgi"

$Body = @{
    username = "rafael.flores"
    password = "nef@2212"
    system   = "GRP_TESTE_API"
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