"""
Checa se existe uma versão mais nova do ACE Helper publicada nos
Releases do GitHub. Não baixa nem substitui nada sozinho — só avisa e
abre a página de download no navegador, se o usuário confirmar.
"""

import webbrowser
import requests

REPO = "Jadissonr/Ace-helper"
RELEASES_API = f"https://api.github.com/repos/{REPO}/releases/latest"
RELEASES_PAGE = f"https://github.com/{REPO}/releases/latest"


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


def check_for_update(current_version: str, timeout: int = 6):
    """
    Retorna (tem_atualizacao: bool, versao_mais_recente: str | None, mensagem: str).
    Nunca levanta exceção — qualquer falha de rede só resulta em
    tem_atualizacao=False, pra não incomodar o usuário se a checagem
    falhar (ex: sem internet no momento).
    """
    try:
        resp = requests.get(RELEASES_API, timeout=timeout)
        if resp.status_code != 200:
            return False, None, "Não foi possível checar atualizações."

        data = resp.json()
        latest_tag = data.get("tag_name", "")
        if not latest_tag:
            return False, None, "Release mais recente não informou uma versão."

        if _parse_version(latest_tag) > _parse_version(current_version):
            return True, latest_tag, f"Nova versão disponível: {latest_tag}"

        return False, latest_tag, "Você já está na versão mais recente."

    except requests.exceptions.RequestException as e:
        return False, None, f"Erro ao checar atualização: {e}"
    except Exception as e:
        return False, None, f"Erro inesperado ao checar atualização: {e}"


def open_releases_page():
    try:
        webbrowser.open(RELEASES_PAGE)
        return True
    except Exception:
        return False
