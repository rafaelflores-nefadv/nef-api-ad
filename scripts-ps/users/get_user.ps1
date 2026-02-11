$BaseUrl = "http://192.168.200.8:8025/api/users/get.cgi"

function Test-GetUser {
    param(
        [Parameter(Mandatory=$true)]
        [string]$SamAccountName
    )

    $url = "$($script:BaseUrl)?sAMAccountName=$SamAccountName"

    Write-Host "`n=== GET USER TEST ==="
    Write-Host "Request:"
    Write-Host $url
    Write-Host ""

    try {
        $response = Invoke-RestMethod `
            -Uri $url `
            -Method GET

        Write-Host "Response:"
        $response | ConvertTo-Json -Depth 6
    }
    catch {
        Write-Host "ERROR:"
        Write-Host $_.Exception.Message
    }
}

Test-GetUser -SamAccountName "teste.api"