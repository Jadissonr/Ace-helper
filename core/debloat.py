"""
Módulo responsável por remover (e tentar restaurar) apps UWP
pré-instalados do Windows. Usa PowerShell por baixo, pois manipulação
de pacotes Appx não é exposta por um módulo nativo do Python.

Filosofia de reversibilidade: a remoção aqui é feita SÓ para o usuário
atual (sem -AllUsers e sem remover o pacote provisionado), o que
mantém os arquivos do app em cache no Windows. Isso é o que permite o
"Restaurar" funcionar na maioria dos casos sem precisar reinstalar
pela Microsoft Store.
"""

import subprocess
import json
import os

from core.logger import log

DATA_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "debloat_list.json")


def load_debloat_list():
    """Carrega a lista de apps disponíveis para remoção a partir do JSON."""
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def get_standard_apps(apps: list) -> list:
    """Retorna apenas os apps marcados como 'standard' (bloatware comum,
    seguro de remover para a maioria dos usuários)."""
    return [a for a in apps if a.get("standard", False)]


def _run_powershell(script: str, timeout: int = 60):
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script],
            capture_output=True, text=True, timeout=timeout
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except FileNotFoundError:
        return -1, "", "PowerShell não disponível neste sistema."
    except subprocess.TimeoutExpired:
        return -1, "", "Tempo esgotado."


def is_installed(app: dict) -> bool:
    """Verifica se o app ainda está instalado para o usuário atual."""
    script = (
        f'if (Get-AppxPackage -Name "{app["appx_name"]}") '
        f'{{ Write-Output "ACE_HELPER_SIM" }} else {{ Write-Output "ACE_HELPER_NAO" }}'
    )
    _, stdout, _ = _run_powershell(script, timeout=20)
    return "ACE_HELPER_SIM" in stdout


def remove_app(app: dict):
    """Remove o app para o usuário atual. Retorna (sucesso, mensagem)."""
    log(f"Removendo app: {app['nome']} ({app['appx_name']})")

    script = f"""
$ErrorActionPreference = 'Stop'
try {{
    $pkg = Get-AppxPackage -Name "{app['appx_name']}" -ErrorAction SilentlyContinue
    if ($pkg) {{
        $pkg | Remove-AppxPackage -ErrorAction Stop
        Write-Output "ACE_HELPER_OK"
    }} else {{
        Write-Output "ACE_HELPER_JA_REMOVIDO"
    }}
}} catch {{
    Write-Output "ACE_HELPER_ERRO: $($_.Exception.Message)"
    exit 1
}}
"""
    returncode, stdout, stderr = _run_powershell(script, timeout=120)

    if "ACE_HELPER_OK" in stdout:
        log(f"Sucesso: {app['nome']} removido.")
        return True, f"{app['nome']} removido."
    elif "ACE_HELPER_JA_REMOVIDO" in stdout:
        return True, f"{app['nome']} já estava removido."
    else:
        erro = stderr or stdout
        log(f"Falha ao remover {app['nome']}: {erro}")
        return False, f"Falha ao remover {app['nome']}: {erro}"


def restore_app(app: dict):
    """
    Tenta restaurar o app removido, reaproveitando os arquivos que
    ainda estão em cache em C:\\Program Files\\WindowsApps (funciona na
    maioria dos casos, já que a remoção não apaga esses arquivos).
    Se não encontrar o cache, orienta reinstalar pela Microsoft Store.
    """
    log(f"Tentando restaurar app: {app['nome']} ({app['appx_name']})")

    script = f"""
$ErrorActionPreference = 'Stop'
try {{
    $pkg = Get-AppxPackage -Name "{app['appx_name']}" -ErrorAction SilentlyContinue
    if ($pkg) {{
        Write-Output "ACE_HELPER_JA_INSTALADO"
    }} else {{
        $dir = Get-ChildItem -Path "$Env:ProgramFiles\\WindowsApps" -Filter "{app['appx_name']}*" -Directory -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($dir) {{
            Add-AppxPackage -DisableDevelopmentMode -Register "$($dir.FullName)\\AppXManifest.xml" -ErrorAction Stop
            Write-Output "ACE_HELPER_OK"
        }} else {{
            Write-Output "ACE_HELPER_NAO_ENCONTRADO"
        }}
    }}
}} catch {{
    Write-Output "ACE_HELPER_ERRO: $($_.Exception.Message)"
    exit 1
}}
"""
    returncode, stdout, stderr = _run_powershell(script, timeout=60)

    if "ACE_HELPER_OK" in stdout:
        log(f"Sucesso: {app['nome']} restaurado.")
        return True, f"{app['nome']} restaurado."
    elif "ACE_HELPER_JA_INSTALADO" in stdout:
        return True, f"{app['nome']} já estava instalado."
    elif "ACE_HELPER_NAO_ENCONTRADO" in stdout:
        msg = f"{app['nome']} não foi encontrado em cache — reinstale pela Microsoft Store."
        log(msg)
        return False, msg
    else:
        erro = stderr or stdout
        log(f"Falha ao restaurar {app['nome']}: {erro}")
        return False, f"Falha ao restaurar {app['nome']}: {erro}"


def remove_multiple(apps: list, progress_callback=None):
    resultados = []
    for app in apps:
        sucesso, mensagem = remove_app(app)
        resultados.append((app["nome"], sucesso, mensagem))
        if progress_callback:
            progress_callback(app["nome"], sucesso, mensagem)
    return resultados


def restore_multiple(apps: list, progress_callback=None):
    resultados = []
    for app in apps:
        sucesso, mensagem = restore_app(app)
        resultados.append((app["nome"], sucesso, mensagem))
        if progress_callback:
            progress_callback(app["nome"], sucesso, mensagem)
    return resultados
