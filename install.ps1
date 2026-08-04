# ACE Helper - Instalador rápido via PowerShell
# Uso:
#   irm https://raw.githubusercontent.com/Jadissonr/Ace-helper/main/install.ps1 | iex

$ErrorActionPreference = "Stop"

# --- CONFIGURE AQUI depois de criar o repositório ---
$repo = "Jadissonr/Ace-helper"
# -----------------------------------------------------

Write-Host "ACE Helper - baixando última versão..." -ForegroundColor Cyan

try {
    $release = Invoke-RestMethod -Uri "https://api.github.com/repos/$repo/releases/latest"
} catch {
    Write-Host "Não foi possível encontrar um release publicado em '$repo'." -ForegroundColor Red
    Write-Host "Verifique se o repositório existe e se já há um Release com o .exe anexado." -ForegroundColor Yellow
    exit 1
}

$asset = $release.assets | Where-Object { $_.name -like "*.exe" } | Select-Object -First 1

if (-not $asset) {
    Write-Host "Nenhum executável (.exe) encontrado no último release de '$repo'." -ForegroundColor Red
    exit 1
}

$dest = Join-Path $env:TEMP "ACEHelper.exe"

Write-Host "Baixando $($asset.name)..." -ForegroundColor Cyan
Invoke-WebRequest -Uri $asset.browser_download_url -OutFile $dest

Write-Host "Executando ACE Helper (vai pedir permissão de administrador)..." -ForegroundColor Green
Start-Process -FilePath $dest
