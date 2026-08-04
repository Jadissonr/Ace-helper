"""
Módulo responsável por instalar plataformas de jogos e aplicativos
via winget (Windows Package Manager), já nativo no Windows 10/11.
"""

import subprocess
import json
import os

from core.logger import log

DATA_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "games_list.json")


def load_games_list():
    """Carrega a lista de plataformas/jogos disponíveis a partir do JSON."""
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def is_winget_available() -> bool:
    """Verifica se o winget está disponível no sistema."""
    try:
        result = subprocess.run(
            ["winget", "--version"],
            capture_output=True, text=True, timeout=10
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def install_app(winget_id: str, nome: str):
    """Instala um app via winget. Retorna (sucesso: bool, mensagem: str)."""
    log(f"Iniciando instalação: {nome} ({winget_id})")

    try:
        result = subprocess.run(
            [
                "winget", "install",
                "--id", winget_id,
                "-e",
                "--silent",
                "--accept-package-agreements",
                "--accept-source-agreements",
            ],
            capture_output=True, text=True, timeout=600
        )

        if result.returncode == 0:
            log(f"Sucesso: {nome} instalado.")
            return True, f"{nome} instalado com sucesso."
        else:
            erro = result.stderr.strip() or result.stdout.strip()
            log(f"Falha ao instalar {nome}: {erro}")
            return False, f"Falha ao instalar {nome}: {erro}"

    except subprocess.TimeoutExpired:
        log(f"Timeout ao instalar {nome}")
        return False, f"Tempo esgotado ao instalar {nome}."
    except Exception as e:
        log(f"Erro inesperado ao instalar {nome}: {e}")
        return False, f"Erro inesperado ao instalar {nome}: {e}"


def install_multiple(apps: list, progress_callback=None):
    """
    Instala uma lista de apps em sequência.
    apps: lista de dicts com 'nome' e 'winget_id'
    progress_callback: função chamada após cada instalação com (nome, sucesso, mensagem)
    """
    resultados = []
    for app in apps:
        sucesso, mensagem = install_app(app["winget_id"], app["nome"])
        resultados.append((app["nome"], sucesso, mensagem))
        if progress_callback:
            progress_callback(app["nome"], sucesso, mensagem)
    return resultados
