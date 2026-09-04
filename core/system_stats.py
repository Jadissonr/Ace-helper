"""
Coleta estatísticas básicas do sistema (CPU, RAM, disco) pro painel
"Início" do app. Usa a biblioteca psutil — leve, multiplataforma,
padrão de fato pra esse tipo de coisa em Python.
"""

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    psutil = None
    PSUTIL_AVAILABLE = False


def get_stats():
    """
    Retorna um dict com cpu_percent, ram_percent, ram_used_gb,
    ram_total_gb, disk_percent (unidade do sistema). Todos os valores
    são None se o psutil não estiver disponível.
    """
    if not PSUTIL_AVAILABLE:
        return {
            "cpu_percent": None,
            "ram_percent": None,
            "ram_used_gb": None,
            "ram_total_gb": None,
            "disk_percent": None,
        }

    try:
        cpu = psutil.cpu_percent(interval=None)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage("C:\\" if _is_windows() else "/")

        return {
            "cpu_percent": cpu,
            "ram_percent": mem.percent,
            "ram_used_gb": round(mem.used / (1024 ** 3), 1),
            "ram_total_gb": round(mem.total / (1024 ** 3), 1),
            "disk_percent": disk.percent,
        }
    except Exception:
        return {
            "cpu_percent": None,
            "ram_percent": None,
            "ram_used_gb": None,
            "ram_total_gb": None,
            "disk_percent": None,
        }


def _is_windows():
    import os
    return os.name == "nt"


def is_admin() -> bool:
    """Verifica se o processo atual está rodando com privilégios de administrador."""
    if not _is_windows():
        return False
    try:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False
