"""
Cria pontos de restauração do Windows antes de qualquer alteração de
registro feita pelo módulo de Tweaks. Isso dá ao usuário uma forma de
desfazer tudo pelo painel de recuperação do Windows, além do botão
"Reverter" do próprio app.

A criação de Restore Points não tem um módulo nativo no Python, então
usamos PowerShell por baixo (mesma abordagem usada pelo WinUtil).
"""

import subprocess
import datetime
import os

from core.logger import log

_NO_WINDOW_FLAGS = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0


def create_restore_point(description: str = None):
    """
    Cria um ponto de restauração do Windows.
    Retorna (sucesso: bool, mensagem: str).
    """
    if description is None:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        description = f"ACE Helper - antes de aplicar tweaks ({timestamp})"

    log(f"Criando ponto de restauração: {description}")

    # Remove temporariamente o limite de "1 ponto a cada 24h" do Windows
    # (senão o Checkpoint-Computer é ignorado silenciosamente se já
    # existir um ponto recente) e garante que o System Restore esteja
    # habilitado na unidade do sistema.
    powershell_script = f"""
$ErrorActionPreference = 'Stop'
try {{
    Set-ItemProperty -Path "HKLM:\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\SystemRestore" -Name "SystemRestorePointCreationFrequency" -Value 0 -ErrorAction SilentlyContinue
    if (-not (Get-ComputerRestorePoint)) {{
        Enable-ComputerRestore -Drive $Env:SystemDrive
    }}
    Checkpoint-Computer -Description "{description}" -RestorePointType MODIFY_SETTINGS
    Write-Output "ACE_HELPER_OK"
}} catch {{
    Write-Output "ACE_HELPER_ERRO: $($_.Exception.Message)"
    exit 1
}}
"""

    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", powershell_script],
            capture_output=True, text=True, timeout=120,
            creationflags=_NO_WINDOW_FLAGS
        )

        output = result.stdout.strip()

        if result.returncode == 0 and "ACE_HELPER_OK" in output:
            log("Ponto de restauração criado com sucesso.")
            return True, "Ponto de restauração criado."
        else:
            erro = result.stderr.strip() or output
            log(f"Falha ao criar ponto de restauração: {erro}")
            return False, f"Não foi possível criar o ponto de restauração: {erro}"

    except FileNotFoundError:
        # Acontece fora do Windows (ex: rodando neste sandbox de teste).
        log("PowerShell não encontrado — pulando criação de ponto de restauração.")
        return False, "PowerShell não disponível neste sistema."
    except subprocess.TimeoutExpired:
        log("Timeout ao criar ponto de restauração.")
        return False, "Tempo esgotado ao criar ponto de restauração."
    except Exception as e:
        log(f"Erro inesperado ao criar ponto de restauração: {e}")
        return False, f"Erro inesperado ao criar ponto de restauração: {e}"
