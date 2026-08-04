"""
Resolve caminhos de assets (imagens, ícones) tanto rodando do código-fonte
quanto de dentro de um .exe compilado com PyInstaller (que extrai os
arquivos pra uma pasta temporária em sys._MEIPASS).
"""

import os
import sys


def resource_path(*parts: str) -> str:
    base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(base_path, *parts)
