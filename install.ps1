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

# Instala num local permanente (não na pasta temp) pra o atalho da
# área de trabalho continuar funcionando depois de reiniciar o PC ou
# o Windows limpar arquivos temporários.
$installDir = Join-Path $env:LOCALAPPDATA "ACEHelper"
if (-not (Test-Path $installDir)) {
    New-Item -ItemType Directory -Path $installDir | Out-Null
}
$dest = Join-Path $installDir "ACEHelper.exe"

Write-Host "Baixando $($asset.name)..." -ForegroundColor Cyan
Invoke-WebRequest -Uri $asset.browser_download_url -OutFile $dest

# Cria o atalho na área de trabalho, se ainda não existir.
$desktopPath = [Environment]::GetFolderPath("Desktop")
$shortcutPath = Join-Path $desktopPath "ACE Helper.lnk"

if (-not (Test-Path $shortcutPath)) {
    Write-Host "Criando atalho na área de trabalho..." -ForegroundColor Cyan
    try {
        $WshShell = New-Object -ComObject WScript.Shell
        $Shortcut = $WshShell.CreateShortcut($shortcutPath)
        $Shortcut.TargetPath = $dest
        $Shortcut.WorkingDirectory = $installDir
        $Shortcut.IconLocation = $dest
        $Shortcut.Description = "ACE Helper - Otimização para Windows"
        $Shortcut.Save()
        Write-Host "Atalho criado." -ForegroundColor Green
    } catch {
        Write-Host "Não foi possível criar o atalho automaticamente (não é um erro grave)." -ForegroundColor Yellow
    }
}

Write-Host "Executando ACE Helper (vai pedir permissão de administrador)..." -ForegroundColor Green
Start-Process -FilePath $dest
