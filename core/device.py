"""
Obtém um identificador único e estável do dispositivo (device
fingerprint), usado para lembrar que essa máquina já validou a chave
de acesso antes, sem precisar guardar a chave em si localmente.

Usa o MachineGuid do Windows (gerado uma vez na instalação do sistema
operacional, único por instalação) em vez do serial da placa-mãe,
porque muita placa OEM retorna esse serial vazio ou genérico — o
MachineGuid é bem mais confiável de se obter.
"""

try:
    import winreg
    WINREG_AVAILABLE = True
except ImportError:
    winreg = None
    WINREG_AVAILABLE = False


def get_device_id():
    """Retorna o MachineGuid do Windows, ou None se não disponível
    (ex: rodando fora do Windows)."""
    if not WINREG_AVAILABLE:
        return None
    try:
        key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Microsoft\Cryptography",
            0,
            winreg.KEY_READ | winreg.KEY_WOW64_64KEY,
        )
        value, _ = winreg.QueryValueEx(key, "MachineGuid")
        winreg.CloseKey(key)
        return value
    except Exception:
        return None
