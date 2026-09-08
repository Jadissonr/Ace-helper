"""
Ferramentas de otimização de rede: limpar cache de DNS, trocar o
servidor DNS (Cloudflare/Google), resetar a pilha TCP/IP, e um teste
rápido de latência até alguns servidores de referência.
"""

import subprocess
import os
import socket
import time

from core.logger import log

_NO_WINDOW_FLAGS = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0

DNS_PROVIDERS = {
    "cloudflare": ("1.1.1.1", "1.0.0.1"),
    "google": ("8.8.8.8", "8.8.4.4"),
}

PING_TARGETS = [
    ("Cloudflare", "1.1.1.1"),
    ("Google", "8.8.8.8"),
    ("Steam", "steamcommunity.com"),
    ("Riot Games", "riotgames.com"),
]


def _run_ps(script, timeout=30):
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script],
            capture_output=True, text=True, timeout=timeout,
            creationflags=_NO_WINDOW_FLAGS
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except FileNotFoundError:
        return -1, "", "PowerShell não disponível neste sistema."
    except subprocess.TimeoutExpired:
        return -1, "", "Tempo esgotado."


def _run_cmd(args, timeout=30):
    try:
        result = subprocess.run(
            args, capture_output=True, text=True, timeout=timeout,
            creationflags=_NO_WINDOW_FLAGS
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except FileNotFoundError:
        return -1, "", "Comando não encontrado neste sistema."
    except subprocess.TimeoutExpired:
        return -1, "", "Tempo esgotado."


def flush_dns():
    """Limpa o cache de DNS local. Retorna (sucesso, mensagem)."""
    log("Limpando cache de DNS...")
    code, out, err = _run_cmd(["ipconfig", "/flushdns"])
    if code == 0:
        log("Cache de DNS limpo.")
        return True, "Cache de DNS limpo com sucesso."
    msg = f"Falha ao limpar cache de DNS: {err or out}"
    log(msg)
    return False, msg


def reset_tcpip():
    """Reseta a pilha TCP/IP (winsock + interface IP). Precisa reiniciar
    o PC pra ter efeito completo. Retorna (sucesso, mensagem)."""
    log("Resetando pilha TCP/IP...")
    code1, out1, err1 = _run_cmd(["netsh", "winsock", "reset"])
    code2, out2, err2 = _run_cmd(["netsh", "int", "ip", "reset"])
    if code1 == 0 and code2 == 0:
        msg = "Pilha TCP/IP resetada. É necessário reiniciar o PC pra concluir."
        log(msg)
        return True, msg
    msg = f"Falha ao resetar TCP/IP: {err1 or out1} {err2 or out2}".strip()
    log(msg)
    return False, msg


def _get_active_adapter_name():
    code, out, _err = _run_ps(
        "(Get-NetAdapter | Where-Object {$_.Status -eq 'Up'} | Select-Object -First 1 -ExpandProperty Name)"
    )
    if code == 0 and out:
        return out.strip()
    return None


def set_dns(provider: str):
    """Configura o DNS do adaptador de rede ativo pro provedor
    indicado ('cloudflare' ou 'google'). Retorna (sucesso, mensagem)."""
    if provider not in DNS_PROVIDERS:
        return False, "Provedor de DNS inválido."

    adapter = _get_active_adapter_name()
    if not adapter:
        return False, "Não foi possível identificar o adaptador de rede ativo."

    primary, secondary = DNS_PROVIDERS[provider]
    log(f"Configurando DNS ({provider}) no adaptador '{adapter}'...")

    script = (
        f"Set-DnsClientServerAddress -InterfaceAlias '{adapter}' "
        f"-ServerAddresses ('{primary}','{secondary}')"
    )
    code, out, err = _run_ps(script)
    if code == 0:
        msg = f"DNS alterado para {provider.capitalize()} ({primary} / {secondary})."
        log(msg)
        return True, msg
    msg = f"Falha ao configurar DNS: {err or out}"
    log(msg)
    return False, msg


def restore_dns_dhcp():
    """Restaura o DNS automático (fornecido pelo roteador/provedor).
    Retorna (sucesso, mensagem)."""
    adapter = _get_active_adapter_name()
    if not adapter:
        return False, "Não foi possível identificar o adaptador de rede ativo."

    log(f"Restaurando DNS automático no adaptador '{adapter}'...")
    script = f"Set-DnsClientServerAddress -InterfaceAlias '{adapter}' -ResetServerAddresses"
    code, out, err = _run_ps(script)
    if code == 0:
        msg = "DNS restaurado para automático (DHCP)."
        log(msg)
        return True, msg
    msg = f"Falha ao restaurar DNS: {err or out}"
    log(msg)
    return False, msg


def ping_test():
    """
    Testa a latência até alguns servidores de referência, medindo o
    tempo de um handshake TCP na porta 443 (em vez de ICMP/ping
    tradicional, pra não depender de permissões de firewall) — uma
    boa aproximação de latência de rede.
    Retorna uma lista de tuplas (nome, host, latencia_ms | None).
    """
    resultados = []
    for nome, host in PING_TARGETS:
        try:
            inicio = time.time()
            with socket.create_connection((host, 443), timeout=3):
                pass
            latencia_ms = round((time.time() - inicio) * 1000)
            resultados.append((nome, host, latencia_ms))
        except Exception:
            resultados.append((nome, host, None))
    return resultados
