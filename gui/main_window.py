"""
Janela principal do ACE Helper (visual CustomTkinter — tema preto/roxo).
Monta a interface com abas: Instalar Jogos, Tweaks e Debloat.
"""

import os
import sys
import customtkinter as ctk
from PIL import Image

from gui.installer_tab import InstallerTab
from gui.tweaks_tab import TweaksTab
from gui.debloat_tab import DebloatTab

APP_NAME = "ACE Helper"
APP_VERSION = "0.3.0"

# Paleta preto + roxo claro
BG_COLOR = "#0a0a0c"
SURFACE_COLOR = "#151517"
ACCENT_COLOR = "#a78bfa"
ACCENT_HOVER = "#8b6cf0"


def _resource_path(relative_path: str) -> str:
    """Resolve o caminho de um asset tanto rodando do código-fonte
    quanto rodando de dentro de um .exe compilado com PyInstaller
    (que extrai os arquivos pra uma pasta temporária em sys._MEIPASS)."""
    base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(base_path, relative_path)


LOGO_PATH = _resource_path(os.path.join("assets", "logo_transparent.png"))
ICON_PATH = _resource_path(os.path.join("assets", "icon.ico"))


class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")  # base; sobrescrevemos as cores manualmente abaixo

        self.title(f"{APP_NAME} v{APP_VERSION}")
        self.geometry("680x600")
        self.minsize(560, 480)
        self.configure(fg_color=BG_COLOR)

        if os.path.exists(ICON_PATH):
            try:
                self.iconbitmap(ICON_PATH)
            except Exception:
                pass  # iconbitmap com .ico só funciona no Windows; ignora fora dele

        self._build_ui()

    def _build_ui(self):
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(20, 5))

        if os.path.exists(LOGO_PATH):
            logo_pil = Image.open(LOGO_PATH)
            logo_w, logo_h = logo_pil.size
            target_h = 42
            target_w = int(logo_w * (target_h / logo_h))
            logo_image = ctk.CTkImage(
                light_image=logo_pil,
                dark_image=logo_pil,
                size=(target_w, target_h)
            )
            logo_label = ctk.CTkLabel(header_frame, image=logo_image, text="")
            logo_label.pack(side="left", padx=(0, 14))

        title_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_frame.pack(side="left")

        header = ctk.CTkLabel(
            title_frame,
            text=APP_NAME,
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=ACCENT_COLOR
        )
        header.pack(anchor="w")

        subheader = ctk.CTkLabel(
            title_frame,
            text="Otimização, debloat e instalação de plataformas de jogos para Windows",
            font=ctk.CTkFont(size=12),
            text_color="gray60"
        )
        subheader.pack(anchor="w", pady=(2, 0))

        tabview = ctk.CTkTabview(
            self,
            fg_color=SURFACE_COLOR,
            segmented_button_fg_color=BG_COLOR,
            segmented_button_selected_color=ACCENT_COLOR,
            segmented_button_selected_hover_color=ACCENT_HOVER,
            segmented_button_unselected_color=BG_COLOR,
            text_color="white",
        )
        tabview.pack(fill="both", expand=True, padx=15, pady=15)

        tab_instalar = tabview.add("Instalar Jogos")
        tab_tweaks = tabview.add("Tweaks")
        tab_debloat = tabview.add("Debloat")

        InstallerTab(tab_instalar).pack(fill="both", expand=True)
        TweaksTab(tab_tweaks).pack(fill="both", expand=True)
        DebloatTab(tab_debloat).pack(fill="both", expand=True)
