"""
Logger simples do ACE Helper.
Registra cada ação executada (instalação, tweak, debloat) em um arquivo
de log com timestamp, para auditoria e para debug.
"""

import os
import datetime

LOG_DIR = os.path.join(os.path.expanduser("~"), "ACEHelper", "logs")
LOG_FILE = os.path.join(LOG_DIR, "ace_helper.log")


def _ensure_log_dir():
    os.makedirs(LOG_DIR, exist_ok=True)


def log(message: str):
    """Escreve uma linha no log com timestamp e retorna a linha formatada
    (útil para exibir também na interface)."""
    _ensure_log_dir()
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {message}"

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")

    return line
