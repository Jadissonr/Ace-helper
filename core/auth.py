"""
Valida a chave de acesso do ACE Helper contra um Cloudflare Worker
remoto. A lista de chaves válidas nunca fica no código-fonte nem no
executável — só no Worker, que você controla e pode atualizar (add ou
revogar chaves) sem recompilar o app.

Usa a biblioteca 'requests' em vez do urllib nativo porque ela lida
melhor com a negociação TLS/SSL em instalações Windows/Python variadas
(o urllib puro deu erro de handshake SSL em alguns ambientes).

Depois de validada uma vez com sucesso, essa máquina fica "lembrada"
(cache local vinculado ao MachineGuid do Windows) e não precisa
validar de novo nas próximas aberturas — ver is_device_authorized() e
save_device_authorization().
"""

import os
import json
import requests

from core.device import get_device_id

# Troque pela URL do seu Worker depois de publicá-lo no Cloudflare
# (painel do Cloudflare -> Workers & Pages -> seu worker -> a URL
# aparece no topo da página, algo como
# https://ace-helper-auth.<seu-subdominio>.workers.dev).
WORKER_URL = "https://SEU-WORKER.SEU-SUBDOMINIO.workers.dev"

AUTH_CACHE_FILE = os.path.join(os.path.expanduser("~"), "ACEHelper", "auth_cache.json")


def validate_key(key: str, timeout: int = 10):
    """Retorna (valido: bool, mensagem: str)."""
    key = (key or "").strip()
    if not key:
        return False, "Digite uma chave de acesso."

    if "SEU-WORKER" in WORKER_URL:
        return False, "WORKER_URL ainda não foi configurada em core/auth.py."

    try:
        resp = requests.post(WORKER_URL, json={"key": key}, timeout=timeout)
        data = resp.json()
        if data.get("valid"):
            return True, "Chave válida."
        return False, "Chave de acesso inválida."
    except requests.exceptions.SSLError as e:
        return False, f"Erro de conexão segura (SSL) com o servidor de validação: {e}"
    except requests.exceptions.ConnectionError as e:
        return False, f"Não foi possível conectar ao servidor de validação: {e}"
    except requests.exceptions.Timeout:
        return False, "Tempo esgotado ao validar a chave. Verifique sua internet."
    except Exception as e:
        return False, f"Erro ao validar chave: {e}"


def is_device_authorized() -> bool:
    """Verifica se essa máquina já validou a chave antes (cache local
    vinculado ao MachineGuid do Windows)."""
    device_id = get_device_id()
    if not device_id or not os.path.exists(AUTH_CACHE_FILE):
        return False
    try:
        with open(AUTH_CACHE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("device_id") == device_id
    except Exception:
        return False


def save_device_authorization():
    """Salva localmente que essa máquina (MachineGuid) já validou a
    chave, pra não pedir de novo nas próximas aberturas."""
    device_id = get_device_id()
    if not device_id:
        return
    try:
        os.makedirs(os.path.dirname(AUTH_CACHE_FILE), exist_ok=True)
        with open(AUTH_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump({"device_id": device_id}, f)
    except Exception:
        pass  # se não conseguir salvar o cache, só volta a pedir a chave da próxima vez
