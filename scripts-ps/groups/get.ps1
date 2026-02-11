# ===============================
# CONFIG
# ===============================

$GroupName = "sicoob_cocre"
$Url = "http://192.168.200.8:8025/api/groups/get.cgi?group=$GroupName"

# ===============================
# REQUEST
# ===============================

try {
    $Response = Invoke-RestMethod `
        -Uri $Url `
        -Method GET

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
