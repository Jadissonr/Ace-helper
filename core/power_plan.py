"""
Gerencia o plano de energia do Windows. O "Ultimate Performance" é um
plano oculto por padrão (não aparece nas opções normais de energia) —
precisa ser duplicado de um GUID de origem fixo do próprio Windows
antes de poder ser ativado. Elimina passos de economia de energia que
podem introduzir microstutters durante jogos.
"""

import subprocess
import os

from core.logger import log

_NO_WINDOW_FLAGS = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0

# GUID fixo, definido pela própria Microsoft, usado pra duplicar o
# plano oculto "Ultimate Performance".
_ULTIMATE_SOURCE_GUID = "e9a42b02-d5df-448d-aa00-03f14749eb61"
# GUID padrão do plano "Balanceado" do Windows (pra reverter).
_BALANCED_GUID = "381b4222-f694-41f0-9685-ff5bb260df2e"


def _run(args, timeout=30):
    try:
        result = subprocess.run(
            args, capture_output=True, text=True, timeout=timeout,
            creationflags=_NO_WINDOW_FLAGS
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except FileNotFoundError:
        return -1, "", "powercfg não disponível neste sistema."
    except subprocess.TimeoutExpired:
        return -1, "", "Tempo esgotado."


def _find_ultimate_guid():
    """Procura o GUID do plano Ultimate Performance, caso já tenha
    sido duplicado antes (powercfg /list mostra todos os planos)."""
    code, out, _err = _run(["powercfg", "/list"])
    if code != 0:
        return None
    for line in out.splitlines():
        if "Ultimate Performance" in line or "Desempenho máximo" in line:
            for token in line.split():
                if len(token) == 36 and token.count("-") == 4:
                    return token
    return None


def get_active_plan_name():
    """Retorna o nome do plano de energia ativo no momento, ou None."""
    code, out, _err = _run(["powercfg", "/getactivescheme"])
    if code != 0 or not out:
        return None
    if "(" in out and ")" in out:
        return out.split("(", 1)[1].rsplit(")", 1)[0]
    return out


def enable_ultimate_performance():
    """Cria (se necessário) e ativa o plano Ultimate Performance.
    Retorna (sucesso, mensagem)."""
    log("Ativando plano de energia Ultimate Performance...")

    guid = _find_ultimate_guid()
    if not guid:
        code, out, err = _run(["powercfg", "-duplicatescheme", _ULTIMATE_SOURCE_GUID])
        if code != 0:
            msg = f"Falha ao criar o plano Ultimate Performance: {err or out}"
            log(msg)
            return False, msg
        guid = _find_ultimate_guid()
        if not guid:
            msg = "Plano criado, mas não foi possível localizá-lo em seguida."
            log(msg)
            return False, msg

    code, out, err = _run(["powercfg", "-setactive", guid])
    if code != 0:
        msg = f"Falha ao ativar o plano: {err or out}"
        log(msg)
        return False, msg

    log("Ultimate Performance ativado.")
    return True, "Plano de energia Ultimate Performance ativado."


def restore_balanced_plan():
    """Reverte pro plano Balanceado (padrão do Windows).
    Retorna (sucesso, mensagem)."""
    log("Restaurando plano de energia Balanceado...")
    code, out, err = _run(["powercfg", "-setactive", _BALANCED_GUID])
    if code != 0:
        msg = f"Falha ao restaurar o plano Balanceado: {err or out}"
        log(msg)
        return False, msg
    log("Plano Balanceado restaurado.")
    return True, "Plano de energia Balanceado restaurado."
