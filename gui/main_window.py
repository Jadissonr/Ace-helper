"""
Janela principal do ACE Helper (visual CustomTkinter — tema preto/roxo).
Monta a interface com abas: Instalar Apps, Tweaks e Debloat.
"""

import os
import threading
import customtkinter as ctk
from PIL import Image

from core.paths import resource_path
from core.feedback import open_feedback_page
from core.updater import check_for_update, open_releases_page
from gui.installer_tab import InstallerTab
from gui.tweaks_tab import TweaksTab
from gui.debloat_tab import DebloatTab

APP_NAME = "ACE Helper"
APP_VERSION = "0.4.0"

# Paleta preto + roxo claro
BG_COLOR = "#0a0a0c"
SURFACE_COLOR = "#151517"
ACCENT_COLOR = "#a78bfa"
ACCENT_HOVER = "#8b6cf0"

LOGO_PATH = resource_path("assets", "logo_transparent.png")
ICON_PATH = resource_path("assets", "icon.ico")


class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")  # base; sobrescrevemos as cores manualmente abaixo

        self.title(f"{APP_NAME} v{APP_VERSION}")
        self.geometry("700x680")
        self.minsize(620, 600)
        self.configure(fg_color=BG_COLOR)

        if os.path.exists(ICON_PATH):
            try:
                self.iconbitmap(ICON_PATH)
            except Exception:
                pass  # iconbitmap com .ico só funciona no Windows; ignora fora dele

        self._build_ui()
        self._check_update_async()

    def _build_ui(self):
        # Layout em grid (em vez de pack) pra área das abas SEMPRE
        # ocupar 100% do espaço restante da janela, sem vãos vazios
        # quando a janela é redimensionada maior que o padrão.
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)  # header
        self.grid_rowconfigure(1, weight=0)  # banner de atualização
        self.grid_rowconfigure(2, weight=1)  # abas (ocupa todo o resto)

        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 5))
        self.header_frame = header_frame

        if os.path.exists(LOGO_PATH):
            logo_pil = Image.open(LOGO_PATH)
            logo_w, logo_h = logo_pil.size
            target_h = 42
            target_w = int(logo_w * (target_h / logo_h))
            logo_image = ctk.CTkImage(
                light_image=logo_pil, dark_image=logo_pil, size=(target_w, target_h)
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
            text="Otimização, debloat e instalação de apps essenciais para gamers e profissionais de esports",
            font=ctk.CTkFont(size=12),
            text_color="gray60"
        )
        subheader.pack(anchor="w", pady=(2, 0))

        btn_feedback = ctk.CTkButton(
            header_frame, text="💬 Feedback", command=self._on_feedback,
            fg_color="transparent", border_width=1, border_color=ACCENT_COLOR,
            text_color=ACCENT_COLOR, hover_color=SURFACE_COLOR,
            width=110
        )
        btn_feedback.pack(side="right", anchor="n")

        # Espaço reservado pro aviso de atualização (populado depois,
        # em segundo plano, se houver uma versão nova disponível).
        # height=0 é importante: sem isso, o CTkFrame usa a altura
        # padrão dele (200px) mesmo vazio, deixando um vão enorme.
        self.update_banner_frame = ctk.CTkFrame(self, fg_color="transparent", height=0)
        self.update_banner_frame.grid(row=1, column=0, sticky="ew", padx=20)

        tabview = ctk.CTkTabview(
            self,
            fg_color=SURFACE_COLOR,
            segmented_button_selected_color=ACCENT_COLOR,
            segmented_button_selected_hover_color=ACCENT_HOVER,
        )
        tabview.grid(row=2, column=0, sticky="nsew", padx=15, pady=15)
        self.tabview = tabview

        tab_instalar = tabview.add("Instalar Apps")
        tab_tweaks = tabview.add("Tweaks")
        tab_debloat = tabview.add("Debloat")

        InstallerTab(tab_instalar).pack(fill="both", expand=True)
        TweaksTab(tab_tweaks).pack(fill="both", expand=True)
        DebloatTab(tab_debloat).pack(fill="both", expand=True)

    def _on_feedback(self):
        sucesso, mensagem = open_feedback_page()
        if not sucesso:
            from tkinter import messagebox
            messagebox.showerror("Feedback", mensagem)

    def _check_update_async(self):
        thread = threading.Thread(target=self._run_check_update, daemon=True)
        thread.start()

    def _run_check_update(self):
        tem_atualizacao, versao, _mensagem = check_for_update(APP_VERSION)
        if tem_atualizacao:
            self.after(0, self._show_update_banner, versao)

    def _show_update_banner(self, versao):
        banner = ctk.CTkFrame(self.update_banner_frame, fg_color="#2a2433", corner_radius=8)
        banner.pack(fill="x", pady=(0, 8))

        inner = ctk.CTkFrame(banner, fg_color="transparent")
        inner.pack(fill="x", padx=12, pady=8)

        label = ctk.CTkLabel(
            inner, text=f"🔔 Nova versão disponível: {versao} (você está na {APP_VERSION})",
            font=ctk.CTkFont(size=11), text_color=ACCENT_COLOR
        )
        label.pack(side="left")

        btn_baixar = ctk.CTkButton(
            inner, text="Baixar atualização", command=open_releases_page,
            fg_color=ACCENT_COLOR, hover_color=ACCENT_HOVER, width=150, height=26
        )
        btn_baixar.pack(side="right")
