"""
Barra lateral de navegação do ACE Helper — substitui as abas no topo
por uma navegação estilo Discord/Spotify: logo no topo, itens de
navegação empilhados, versão no rodapé.
"""

import os
import customtkinter as ctk
from PIL import Image

from core.paths import resource_path
from gui import theme

LOGO_PATH = resource_path("assets", "logo_transparent.png")

NAV_ITEMS = [
    ("home", "🏠", "Início"),
    ("instalar", "📦", "Instalar Apps"),
    ("tweaks", "⚡", "Tweaks"),
    ("rede", "🌐", "Rede"),
    ("startup", "🚀", "Inicialização"),
    ("debloat", "🧹", "Debloat"),
]


class Sidebar(ctk.CTkFrame):
    def __init__(self, parent, on_navigate, app_version: str):
        super().__init__(parent, fg_color=theme.SURFACE, corner_radius=0, width=210)
        self.grid_propagate(False)
        self.on_navigate = on_navigate
        self.nav_buttons = {}
        self.active_key = None

        self._build_ui(app_version)

    def _build_ui(self, app_version):
        self.grid_rowconfigure(2, weight=1)  # espaço flexível antes do rodapé
        self.grid_columnconfigure(0, weight=1)

        # --- Logo ---
        logo_frame = ctk.CTkFrame(self, fg_color="transparent")
        logo_frame.grid(row=0, column=0, sticky="ew", padx=18, pady=(24, 4))

        if os.path.exists(LOGO_PATH):
            logo_pil = Image.open(LOGO_PATH)
            w, h = logo_pil.size
            target_w = 150
            target_h = int(h * (target_w / w))
            logo_img = ctk.CTkImage(light_image=logo_pil, dark_image=logo_pil, size=(target_w, target_h))
            ctk.CTkLabel(logo_frame, image=logo_img, text="").pack(anchor="w")

        ctk.CTkLabel(
            logo_frame, text="ACE HELPER", font=theme.font_heading(11),
            text_color=theme.ACCENT_2
        ).pack(anchor="w", pady=(6, 0))

        # --- separador ---
        sep = ctk.CTkFrame(self, fg_color=theme.BORDER, height=1)
        sep.grid(row=1, column=0, sticky="ew", padx=18, pady=(16, 8))

        # --- itens de navegação ---
        nav_frame = ctk.CTkFrame(self, fg_color="transparent")
        nav_frame.grid(row=1, column=0, sticky="new", padx=10, pady=(30, 0))

        for key, icon, label in NAV_ITEMS:
            btn = ctk.CTkButton(
                nav_frame, text=f"{icon}   {label}",
                anchor="w", font=theme.font_body(13),
                fg_color="transparent", text_color=theme.TEXT_MUTED,
                hover_color=theme.SURFACE_ALT,
                corner_radius=8, height=38,
                command=lambda k=key: self._on_click(k),
            )
            btn.pack(fill="x", pady=2)
            self.nav_buttons[key] = btn

        # --- rodapé: versão ---
        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.grid(row=3, column=0, sticky="ew", padx=18, pady=16)
        ctk.CTkLabel(
            footer, text=f"v{app_version}", font=theme.font_body(10),
            text_color=theme.TEXT_DIM
        ).pack(anchor="w")

    def _on_click(self, key):
        self.set_active(key)
        self.on_navigate(key)

    def set_active(self, key):
        self.active_key = key
        for k, btn in self.nav_buttons.items():
            if k == key:
                btn.configure(fg_color=theme.SURFACE_ALT, text_color=theme.TEXT_PRIMARY)
            else:
                btn.configure(fg_color="transparent", text_color=theme.TEXT_MUTED)
