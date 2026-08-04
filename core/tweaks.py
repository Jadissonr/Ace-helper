"""
Módulo responsável por aplicar e reverter tweaks de registro do Windows.

Cada tweak no JSON tem uma lista de "entries" (uma ou mais chaves de
registro que precisam mudar juntas). Cada entry tem um valor "ativado"
e um valor "original" — isso permite reverter qualquer tweak de volta
ao estado padrão do Windows. Quando "value_original" é null, significa
que a chave não existia por padrão, então reverter = apagar o valor
(mesmo comportamento do "<RemoveEntry>" do WinUtil).

winreg é um módulo nativo do Python, mas só existe no Windows. Em
qualquer outro sistema (ex: ao rodar testes/lint no CI ou neste
sandbox), o import falha — por isso o fallback abaixo, que permite o
resto do app (e os testes de sintaxe) funcionarem normalmente fora do
Windows, sem quebrar o import.
"""

import json
import os

try:
    import winreg
    WINREG_AVAILABLE = True
except ImportError:
    winreg = None
    WINREG_AVAILABLE = False

from core.logger import log

DATA_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "tweaks_list.json")

_TYPE_MAP_NAMES = {
    "DWORD": "REG_DWORD",
    "QWORD": "REG_QWORD",
    "STRING": "REG_SZ",
}


def _get_hive_const(hive_name: str):
    if not WINREG_AVAILABLE:
        raise RuntimeError("winreg só está disponível no Windows.")
    return getattr(winreg, hive_name)


def _get_value_type_const(type_name: str):
    if not WINREG_AVAILABLE:
        raise RuntimeError("winreg só está disponível no Windows.")
    return getattr(winreg, _TYPE_MAP_NAMES[type_name])


def load_tweaks_list():
    """Carrega a lista de tweaks disponíveis a partir do JSON."""
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def get_standard_tweaks(tweaks: list) -> list:
    """Retorna apenas os tweaks marcados como 'standard' (recomendados
    para a maioria dos usuários, seguros e reversíveis)."""
    return [t for t in tweaks if t.get("standard", False)]


def _get_entry_value(entry: dict):
    """Lê o valor atual de uma entrada de registro. None se não existir."""
    if not WINREG_AVAILABLE:
        return None

    hive = _get_hive_const(entry["hive"])
    try:
        with winreg.OpenKey(hive, entry["path"], 0, winreg.KEY_READ) as key:
            value, _ = winreg.QueryValueEx(key, entry["value_name"])
            return value
    except (FileNotFoundError, OSError):
        return None


def is_applied(tweak: dict) -> bool:
    """Um tweak é considerado 'aplicado' quando TODAS as suas entries
    já estão com o valor ativado."""
    if not WINREG_AVAILABLE:
        return False
    return all(
        _get_entry_value(entry) == entry["value_ativado"]
        for entry in tweak["entries"]
    )


def _set_entry(entry: dict, value):
    hive = _get_hive_const(entry["hive"])
    value_type = _get_value_type_const(entry["value_type"])

    key = winreg.CreateKeyEx(hive, entry["path"], 0, winreg.KEY_WRITE)
    try:
        winreg.SetValueEx(key, entry["value_name"], 0, value_type, value)
    finally:
        winreg.CloseKey(key)


def _delete_entry(entry: dict):
    """Remove o valor de registro (usado na reversão quando a chave
    não existia por padrão). Ignora silenciosamente se já não existir."""
    hive = _get_hive_const(entry["hive"])
    try:
        key = winreg.OpenKey(hive, entry["path"], 0, winreg.KEY_WRITE)
        try:
            winreg.DeleteValue(key, entry["value_name"])
        finally:
            winreg.CloseKey(key)
    except (FileNotFoundError, OSError):
        pass


def apply_tweak(tweak: dict):
    """Aplica todas as entries do tweak (valores 'ativado'). Retorna (sucesso, mensagem)."""
    log(f"Aplicando tweak: {tweak['nome']}")
    try:
        for entry in tweak["entries"]:
            _set_entry(entry, entry["value_ativado"])
        log(f"Sucesso: {tweak['nome']} aplicado.")
        return True, f"{tweak['nome']} aplicado."
    except Exception as e:
        log(f"Erro ao aplicar {tweak['nome']}: {e}")
        return False, f"Erro ao aplicar {tweak['nome']}: {e}"


def revert_tweak(tweak: dict):
    """Reverte todas as entries do tweak para o valor original (ou
    apaga o valor, se ele não existia por padrão). Retorna (sucesso, mensagem)."""
    log(f"Revertendo tweak: {tweak['nome']}")
    try:
        for entry in tweak["entries"]:
            if entry["value_original"] is None:
                _delete_entry(entry)
            else:
                _set_entry(entry, entry["value_original"])
        log(f"Sucesso: {tweak['nome']} revertido.")
        return True, f"{tweak['nome']} revertido."
    except Exception as e:
        log(f"Erro ao reverter {tweak['nome']}: {e}")
        return False, f"Erro ao reverter {tweak['nome']}: {e}"


def apply_multiple(tweaks: list, progress_callback=None):
    """Aplica uma lista de tweaks em sequência."""
    resultados = []
    for tweak in tweaks:
        sucesso, mensagem = apply_tweak(tweak)
        resultados.append((tweak["nome"], sucesso, mensagem))
        if progress_callback:
            progress_callback(tweak["nome"], sucesso, mensagem)
    return resultados


def revert_multiple(tweaks: list, progress_callback=None):
    """Reverte uma lista de tweaks em sequência."""
    resultados = []
    for tweak in tweaks:
        sucesso, mensagem = revert_tweak(tweak)
        resultados.append((tweak["nome"], sucesso, mensagem))
        if progress_callback:
            progress_callback(tweak["nome"], sucesso, mensagem)
    return resultados
