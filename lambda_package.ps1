# PowerShell Lambda package script for creating deployment packages

param(
    [Parameter(Mandatory=$true)]
    [string]$HandlerName
)

$ErrorActionPreference = "Stop"

$PackageName = "lambda-$HandlerName.zip"

Write-Host "Creating Lambda deployment package for $HandlerName..." -ForegroundColor Cyan

# Create temporary directory
$TempDir = New-Item -ItemType Directory -Path (Join-Path $env:TEMP ([System.Guid]::NewGuid().ToString()))
Write-Host "Using temp directory: $TempDir"

try {
    # Install dependencies
    Write-Host "Installing dependencies..." -ForegroundColor Yellow
    pip install -r requirements.txt -t $TempDir --quiet

    # Copy source code
    Write-Host "Copying source code..." -ForegroundColor Yellow
    Copy-Item -Path "src" -Destination $TempDir -Recurse

    # Create zip file
    Write-Host "Creating zip file..." -ForegroundColor Yellow
    $ZipPath = Join-Path $PWD $PackageName
    
    # Remove existing package if exists
    if (Test-Path $ZipPath) {
        Remove-Item $ZipPath -Force
    }

    # Compress to zip
    Compress-Archive -Path "$TempDir\*" -DestinationPath $ZipPath -Force

    # Get file size
    $FileSize = (Get-Item $ZipPath).Length / 1MB
    $FileSizeFormatted = "{0:N2} MB" -f $FileSize

    Write-Host "Package created: $PackageName" -ForegroundColor Green
    Write-Host "Size: $FileSizeFormatted" -ForegroundColor Green

} finally {
    # Cleanup
    Write-Host "Cleaning up temp directory..."
    Remove-Item -Path $TempDir -Recurse -Force -ErrorAction SilentlyContinue
}
