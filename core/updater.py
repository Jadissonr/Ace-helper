"""
Checa se existe uma versão mais nova do ACE Helper publicada nos
Releases do GitHub, e pode se auto-atualizar: baixa o novo .exe, fecha
o app, troca o arquivo antigo pelo novo, e reabre — tudo sozinho.

Só funciona rodando como .exe compilado (não faz sentido, e não roda,
a partir do código-fonte via 'python main.py').
"""

import os
import sys
import subprocess
import tempfile
import webbrowser
import requests

from core.logger import log

REPO = "Jadissonr/Ace-helper"
RELEASES_API = f"https://api.github.com/repos/{REPO}/releases/latest"
RELEASES_PAGE = f"https://github.com/{REPO}/releases/latest"

_NO_WINDOW_FLAGS = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0


def _parse_version(v: str):
    """Converte 'v0.10.2' ou '0.10.2' em (0, 10, 2) pra comparar
    corretamente (string comparison sozinha falha em casos tipo
    '0.9.0' vs '0.10.0')."""
    v = v.lstrip("vV")
    parts = []
    for p in v.split("."):
        digits = "".join(ch for ch in p if ch.isdigit())
        parts.append(int(digits) if digits else 0)
    return tuple(parts) if parts else (0,)


def is_frozen() -> bool:
    """True quando rodando de dentro do .exe compilado (PyInstaller)."""
    return getattr(sys, "frozen", False)


def check_for_update(current_version: str, timeout: int = 6):
    """
    Retorna um dict: {has_update, latest_version, download_url, message}.
    Nunca levanta exceção — qualquer falha de rede só resulta em
    has_update=False, pra não incomodar o usuário se a checagem falhar
    (ex: sem internet no momento).
    """
    resultado = {"has_update": False, "latest_version": None, "download_url": None, "message": ""}

    try:
        resp = requests.get(RELEASES_API, timeout=timeout)
        if resp.status_code != 200:
            resultado["message"] = "Não foi possível checar atualizações."
            log(f"check_for_update: status HTTP {resp.status_code} ao consultar {RELEASES_API}")
            return resultado

        data = resp.json()
        latest_tag = data.get("tag_name", "")
        if not latest_tag:
            resultado["message"] = "Release mais recente não informou uma versão."
            log("check_for_update: release mais recente sem tag_name.")
            return resultado

        resultado["latest_version"] = latest_tag

        assets = data.get("assets", [])
        asset = next((a for a in assets if a.get("name", "").endswith(".exe")), None)
        if asset:
            resultado["download_url"] = asset.get("browser_download_url")
        else:
            nomes = [a.get("name", "?") for a in assets]
            log(f"check_for_update: nenhum .exe encontrado nos assets do release {latest_tag}. Assets: {nomes}")

        log(
            f"check_for_update: atual={current_version} | mais_recente={latest_tag} | "
            f"download_url={'OK' if resultado['download_url'] else 'AUSENTE'} | frozen={is_frozen()}"
        )

        if _parse_version(latest_tag) > _parse_version(current_version):
            resultado["has_update"] = True
            resultado["message"] = f"Nova versão disponível: {latest_tag}"
        else:
            resultado["message"] = "Você já está na versão mais recente."

        return resultado

    except requests.exceptions.RequestException as e:
        resultado["message"] = f"Erro ao checar atualização: {e}"
        log(f"check_for_update: erro de rede: {e}")
        return resultado
    except Exception as e:
        resultado["message"] = f"Erro inesperado ao checar atualização: {e}"
        log(f"check_for_update: erro inesperado: {e}")
        return resultado


def open_releases_page():
    try:
        webbrowser.open(RELEASES_PAGE)
        return True
    except Exception:
        return False


def self_update(download_url: str, progress_callback=None):
    """
    Baixa a nova versão do .exe e prepara a troca automática. Se tudo
    correr bem, retorna (True, mensagem) — quem chamou deve fechar o
    app logo em seguida (o script auxiliar espera o processo atual
    encerrar pra fazer a troca e reabrir na versão nova).

    progress_callback(bytes_baixados, bytes_totais) é chamado durante
    o download.
    """
    if not is_frozen():
        return False, "Auto-atualização só funciona na versão compilada (.exe), não rodando do código-fonte."

    if not download_url:
        return False, "URL de download da atualização não encontrada."

    current_exe = sys.executable
    exe_dir = os.path.dirname(current_exe)
    new_exe_path = os.path.join(exe_dir, "ACEHelper_new.exe")

    try:
        log(f"Baixando atualização de {download_url}")
        with requests.get(download_url, stream=True, timeout=60) as r:
            r.raise_for_status()
            total = int(r.headers.get("content-length", 0))
            baixado = 0
            with open(new_exe_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=1024 * 1024):
                    if not chunk:
                        continue
                    f.write(chunk)
                    baixado += len(chunk)
                    if progress_callback and total:
                        progress_callback(baixado, total)
    except Exception as e:
        log(f"Erro ao baixar atualização: {e}")
        return False, f"Erro ao baixar atualização: {e}"

    pid = os.getpid()
    bat_path = os.path.join(tempfile.gettempdir(), "ace_helper_update.bat")
    bat_content = (
        "@echo off\n"
        ":wait_loop\n"
        f'tasklist /FI "PID eq {pid}" 2^>NUL | find /I "{pid}" >NUL\n'
        'if "%ERRORLEVEL%"=="0" (\n'
        "    timeout /t 1 /nobreak >NUL\n"
        "    goto wait_loop\n"
        ")\n"
        f'move /Y "{new_exe_path}" "{current_exe}" >NUL\n'
        f'start "" "{current_exe}"\n'
        'del "%~f0"\n'
    )

    try:
        with open(bat_path, "w", encoding="utf-8") as f:
            f.write(bat_content)

        subprocess.Popen(
            ["cmd", "/c", bat_path],
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
        )
    except Exception as e:
        log(f"Erro ao preparar script de atualização: {e}")
        return False, f"Não foi possível preparar a atualização: {e}"

    log("Atualização baixada, script auxiliar preparado. Fechando pra trocar de versão...")
    return True, "Atualização baixada. O ACE Helper vai fechar e reabrir na nova versão em instantes."
