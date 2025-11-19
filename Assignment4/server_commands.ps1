# PowerShell script for server operations
# Usage: .\server_commands.ps1 [command]
# Replace YOUR_USER_NAME with your actual username

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("download-data", "upload-code", "ssh", "setup")]
    [string]$Command = "help"
)

$SERVER = "YOUR_USER_NAME@51.222.140.217"
$REMOTE_DIR = "~/assignment4_order_router"
$LOCAL_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path

function Download-Data {
    Write-Host "Downloading data files from server..." -ForegroundColor Green
    Write-Host "This may take a while as the quotes file is very large..." -ForegroundColor Yellow
    
    scp "$SERVER`:/opt/assignment3/executions.csv" "$LOCAL_DIR\"
    scp "$SERVER`:/opt/assignment4/quotes_2025-09-10_small.csv.gz" "$LOCAL_DIR\"
    
    Write-Host "Download complete!" -ForegroundColor Green
}

function Upload-Code {
    Write-Host "Uploading code to server..." -ForegroundColor Green
    
    Push-Location $LOCAL_DIR
    
    # Upload Python files
    Get-ChildItem -Filter "*.py" | ForEach-Object {
        Write-Host "Uploading $($_.Name)..." -ForegroundColor Cyan
        scp $_.FullName "$SERVER`:$REMOTE_DIR/"
    }
    
    # Upload models if they exist
    if (Test-Path "models\models.joblib") {
        Write-Host "Uploading models.joblib..." -ForegroundColor Cyan
        scp "models\models.joblib" "$SERVER`:$REMOTE_DIR/"
    }
    
    Pop-Location
    
    Write-Host "Upload complete!" -ForegroundColor Green
}

function SSH-Connect {
    Write-Host "Connecting to server..." -ForegroundColor Green
    ssh $SERVER
}

function Setup-Directory {
    Write-Host "Setting up directory on server..." -ForegroundColor Green
    ssh $SERVER "mkdir -p $REMOTE_DIR && chmod 755 $REMOTE_DIR"
    Write-Host "Directory setup complete!" -ForegroundColor Green
}

function Show-Help {
    Write-Host "Usage: .\server_commands.ps1 [command]" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Commands:"
    Write-Host "  download-data  - Download executions.csv and quotes file from server"
    Write-Host "  upload-code    - Upload Assignment4 code to server"
    Write-Host "  ssh            - SSH into the server"
    Write-Host "  setup          - Create and set permissions on server directory"
    Write-Host ""
    Write-Host "Note: Replace YOUR_USER_NAME in this script with your actual username" -ForegroundColor Red
}

switch ($Command) {
    "download-data" { Download-Data }
    "upload-code" { Upload-Code }
    "ssh" { SSH-Connect }
    "setup" { Setup-Directory }
    default { Show-Help }
}

