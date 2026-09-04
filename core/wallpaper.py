"""
Define o papel de parede da área de trabalho como a logo do ACE, após
a aplicação de tweaks. Usa a API nativa do Windows (SystemParametersInfo)
via ctypes — não precisa de nenhuma dependência externa.
"""

import os
import shutil
import ctypes

from core.paths import resource_path
from core.logger import log

SPI_SETDESKWALLPAPER = 20
SPIF_UPDATEINIFILE = 0x01
SPIF_SENDCHANGE = 0x02

WALLPAPER_SOURCE = resource_path("assets", "wallpaper.png")
# Copiado pra um local permanente antes de aplicar — o Windows precisa
# de um caminho de arquivo estável (a pasta de extração do .exe é
# temporária e pode não existir mais depois que o app fecha).
WALLPAPER_DEST_DIR = os.path.join(os.path.expanduser("~"), "ACEHelper")
WALLPAPER_DEST = os.path.join(WALLPAPER_DEST_DIR, "wallpaper.png")


def set_ace_wallpaper():
    """Define o papel de parede da ACE. Retorna (sucesso, mensagem)."""
    if os.name != "nt":
        return False, "Definir papel de parede só funciona no Windows."

    if not os.path.exists(WALLPAPER_SOURCE):
        msg = "Arquivo de wallpaper não encontrado no app."
        log(msg)
        return False, msg

    try:
        os.makedirs(WALLPAPER_DEST_DIR, exist_ok=True)
        shutil.copyfile(WALLPAPER_SOURCE, WALLPAPER_DEST)

        result = ctypes.windll.user32.SystemParametersInfoW(
            SPI_SETDESKWALLPAPER, 0, WALLPAPER_DEST, SPIF_UPDATEINIFILE | SPIF_SENDCHANGE
        )

        if result:
            log("Papel de parede da ACE definido com sucesso.")
            return True, "Papel de parede da ACE aplicado."
        else:
            msg = "O Windows recusou a troca de papel de parede."
            log(msg)
            return False, msg

    except Exception as e:
        log(f"Erro ao definir papel de parede: {e}")
        return False, f"Erro ao definir papel de parede: {e}"
