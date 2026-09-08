"""
Gerenciador de itens de inicializacao do Windows. Lista programas que
abrem sozinhos com o Windows (chaves de registro Run + atalhos na
pasta "Inicializar") e permite habilitar/desabilitar cada um.

Usa o mesmo mecanismo que o proprio Gerenciador de Tarefas do Windows
usa pra isso - a chave de registro "StartupApproved". Isso significa
que desabilitar um item NAO apaga o registro/atalho original, so marca
como desabilitado - totalmente reversivel, e o item continua aparecendo
no Gerenciador de Tarefas do Windows do jeito certo tambem.
"""

import os
import glob

try:
    import winreg
    WINREG_AVAILABLE = True
except ImportError:
    winreg = None
    WINREG_AVAILABLE = False

from core.logger import log

_RUN_LOCATIONS = [
    ("HKEY_CURRENT_USER", r"Software\Microsoft\Windows\CurrentVersion\Run"),
    ("HKEY_LOCAL_MACHINE", r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"),
    ("HKEY_LOCAL_MACHINE", r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Run"),
]

_APPROVED_RUN_PATHS = {
    "HKEY_CURRENT_USER": r"Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\Run",
    "HKEY_LOCAL_MACHINE": r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\Run",
}

_APPROVED_STARTUP_FOLDER_PATH = r"Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\StartupFolder"


def _hive_const(name):
    return getattr(winreg, name)


def _get_startup_folders():
    folders = []
    appdata = os.environ.get("APPDATA")
    if appdata:
        folders.append(("Usuario atual", os.path.join(
            appdata, "Microsoft", "Windows", "Start Menu", "Programs", "Startup"
        )))
    programdata = os.environ.get("PROGRAMDATA")
    if programdata:
        folders.append(("Todos os usuarios", os.path.join(
            programdata, "Microsoft", "Windows", "Start Menu", "Programs", "Startup"
        )))
    return folders


def _is_approved_enabled(hive_name, approved_path, value_name):
    if not WINREG_AVAILABLE:
        return True
    try:
        hive = _hive_const(hive_name)
        with winreg.OpenKey(hive, approved_path, 0, winreg.KEY_READ) as key:
            data, _ = winreg.QueryValueEx(key, value_name)
            if isinstance(data, (bytes, bytearray)) and len(data) > 0:
                return data[0] == 0x02
            return True
    except FileNotFoundError:
        return True
    except OSError:
        return True


def _set_approved_state(hive_name, approved_path, value_name, enabled):
    hive = _hive_const(hive_name)
    key = winreg.CreateKeyEx(hive, approved_path, 0, winreg.KEY_WRITE)
    try:
        flag = 0x02 if enabled else 0x03
        data = bytes([flag]) + bytes(11)
        winreg.SetValueEx(key, value_name, 0, winreg.REG_BINARY, data)
    finally:
        winreg.CloseKey(key)


def list_startup_items():
    if not WINREG_AVAILABLE:
        return []

    items = []

    for hive_name, run_path in _RUN_LOCATIONS:
        hive = _hive_const(hive_name)
        try:
            with winreg.OpenKey(hive, run_path, 0, winreg.KEY_READ) as key:
                index = 0
                while True:
                    try:
                        name, value, _ = winreg.EnumValue(key, index)
                    except OSError:
                        break
                    index += 1

                    approved_path = _APPROVED_RUN_PATHS.get(hive_name)
                    enabled = (
                        _is_approved_enabled(hive_name, approved_path, name)
                        if approved_path else True
                    )

                    items.append({
                        "id": f"reg::{hive_name}::{run_path}::{name}",
                        "nome": name,
                        "tipo": "registro",
                        "local": "Maquina" if hive_name == "HKEY_LOCAL_MACHINE" else "Usuario atual",
                        "caminho": value,
                        "enabled": enabled,
                        "_hive": hive_name,
                        "_approved_path": approved_path,
                        "_value_name": name,
                    })
        except FileNotFoundError:
            continue
        except OSError:
            continue

    for local_label, folder in _get_startup_folders():
        if not os.path.isdir(folder):
            continue
        try:
            for filepath in glob.glob(os.path.join(folder, "*")):
                filename = os.path.basename(filepath)
                if filename.lower() == "desktop.ini":
                    continue

                enabled = _is_approved_enabled(
                    "HKEY_CURRENT_USER", _APPROVED_STARTUP_FOLDER_PATH, filename
                )

                items.append({
                    "id": f"folder::{local_label}::{filename}",
                    "nome": os.path.splitext(filename)[0],
                    "tipo": "atalho",
                    "local": local_label,
                    "caminho": filepath,
                    "enabled": enabled,
                    "_hive": "HKEY_CURRENT_USER",
                    "_approved_path": _APPROVED_STARTUP_FOLDER_PATH,
                    "_value_name": filename,
                })
        except OSError:
            continue

    return items


def set_item_enabled(item, enabled):
    if not WINREG_AVAILABLE:
        return False, "Este recurso so funciona no Windows."

    approved_path = item.get("_approved_path")
    if not approved_path:
        return False, "Local de registro nao suportado pra esse item."

    try:
        _set_approved_state(item["_hive"], approved_path, item["_value_name"], enabled)
        acao = "habilitado" if enabled else "desabilitado"
        msg = f"{item['nome']} {acao}."
        log(msg)
        return True, msg
    except PermissionError:
        msg = f"Sem permissao pra alterar '{item['nome']}' (tente rodar como administrador)."
        log(msg)
        return False, msg
    except Exception as e:
        msg = f"Erro ao alterar '{item['nome']}': {e}"
        log(msg)
        return False, msg
