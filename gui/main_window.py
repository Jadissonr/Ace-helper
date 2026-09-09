"""
Janela principal do ACE Helper — tema gamer/neon (preto + roxo + ciano),
navegação em barra lateral (sidebar) com 4 páginas: Início, Instalar
Apps, Tweaks e Debloat.
"""

import os
import threading
import customtkinter as ctk

from core.updater import check_for_update, open_releases_page, self_update, is_frozen
from core.paths import resource_path
from core.feedback import open_feedback_page
from gui import theme
from gui.sidebar import Sidebar
from gui.home_tab import HomeTab
from gui.installer_tab import InstallerTab
from gui.tweaks_tab import TweaksTab
from gui.network_tab import NetworkTab
from gui.startup_tab import StartupTab
from gui.debloat_tab import DebloatTab

APP_NAME = "ACE Helper"
APP_VERSION = "0.7.2"

ICON_PATH = resource_path("assets", "icon.ico")

PAGE_TITLES = {
    "home": "Início",
    "instalar": "Instalar Apps",
    "tweaks": "Tweaks",
    "rede": "Rede",
    "startup": "Inicialização",
    "debloat": "Debloat",
}


class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")  # base; sobrescrevemos as cores manualmente

        self.title(f"{APP_NAME} v{APP_VERSION}")
        self.geometry("920x680")
        self.minsize(820, 600)
        self.configure(fg_color=theme.BG)

        if os.path.exists(ICON_PATH):
            try:
                self.iconbitmap(ICON_PATH)
            except Exception:
                pass  # iconbitmap com .ico só funciona no Windows; ignora fora dele

        self.pages = {}
        self._build_ui()
        # Agenda pra depois do mainloop já estar rodando (mesmo motivo
        # do StartupTab — evita corrida entre a thread de rede e o
        # início do mainloop).
        self.after(300, self._check_update_async)

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- Sidebar ---
        sidebar = Sidebar(self, on_navigate=self._navigate, app_version=APP_VERSION)
        sidebar.grid(row=0, column=0, sticky="ns")
        self.sidebar = sidebar

        # --- Área de conteúdo ---
        content = ctk.CTkFrame(self, fg_color=theme.BG, corner_radius=0)
        content.grid(row=0, column=1, sticky="nsew")
        content.grid_columnconfigure(0, weight=1)
        content.grid_rowconfigure(2, weight=1)

        # Barra superior: título da página + feedback
        top_bar = ctk.CTkFrame(content, fg_color="transparent")
        top_bar.grid(row=0, column=0, sticky="ew", padx=24, pady=(22, 4))

        self.page_title_lbl = ctk.CTkLabel(
            top_bar, text=PAGE_TITLES["home"], font=theme.font_display(20),
            text_color=theme.TEXT_PRIMARY
        )
        self.page_title_lbl.pack(side="left")

        btn_feedback = ctk.CTkButton(
            top_bar, text="💬 Feedback", command=self._on_feedback,
            fg_color="transparent", border_width=1, border_color=theme.ACCENT,
            text_color=theme.ACCENT, hover_color=theme.SURFACE_ALT,
            width=110
        )
        btn_feedback.pack(side="right")

        # Espaço reservado pro banner de atualização
        self.update_banner_frame = ctk.CTkFrame(content, fg_color="transparent", height=0)
        self.update_banner_frame.grid(row=1, column=0, sticky="ew", padx=24)

        # --- Container das páginas (empilhadas, mostra uma por vez) ---
        pages_container = ctk.CTkFrame(content, fg_color="transparent")
        pages_container.grid(row=2, column=0, sticky="nsew", padx=24, pady=(10, 20))
        pages_container.grid_columnconfigure(0, weight=1)
        pages_container.grid_rowconfigure(0, weight=1)

        self.pages["home"] = HomeTab(pages_container, on_navigate=self._navigate)
        self.pages["instalar"] = InstallerTab(pages_container)
        self.pages["tweaks"] = TweaksTab(pages_container)
        self.pages["rede"] = NetworkTab(pages_container)
        self.pages["startup"] = StartupTab(pages_container)
        self.pages["debloat"] = DebloatTab(pages_container)

        for page in self.pages.values():
            page.grid(row=0, column=0, sticky="nsew")

        self.sidebar.set_active("home")
        self.pages["home"].tkraise()

    def _navigate(self, key: str):
        if key not in self.pages:
            return
        self.page_title_lbl.configure(text=PAGE_TITLES.get(key, key))
        self.pages[key].tkraise()
        self.sidebar.set_active(key)

    def _on_feedback(self):
        sucesso, mensagem = open_feedback_page()
        if not sucesso:
            from tkinter import messagebox
            messagebox.showerror("Feedback", mensagem)

    def _check_update_async(self):
        thread = threading.Thread(target=self._run_check_update, daemon=True)
        thread.start()

    def _run_check_update(self):
        resultado = check_for_update(APP_VERSION)
        if resultado["has_update"]:
            self.after(0, self._show_update_banner, resultado)

    def _show_update_banner(self, resultado):
        versao = resultado["latest_version"]
        download_url = resultado["download_url"]

        banner = theme.glow_card(self.update_banner_frame, fg_color="#241f30", border_color=theme.ACCENT)
        banner.pack(fill="x", pady=(0, 8))

        inner = ctk.CTkFrame(banner, fg_color="transparent")
        inner.pack(fill="x", padx=12, pady=8)

        self.update_label = ctk.CTkLabel(
            inner, text=f"🔔 Nova versão disponível: {versao} (você está na {APP_VERSION})",
            font=theme.font_body(11), text_color=theme.ACCENT_GLOW
        )
        self.update_label.pack(side="left")

        if is_frozen():
            self.btn_atualizar_agora = ctk.CTkButton(
                inner, text="Atualizar agora", command=lambda: self._on_atualizar_agora(download_url),
                fg_color=theme.ACCENT, hover_color=theme.ACCENT_HOVER, width=130, height=26
            )
            self.btn_atualizar_agora.pack(side="right", padx=(6, 0))
        else:
            btn_baixar = ctk.CTkButton(
                inner, text="Baixar atualização", command=open_releases_page,
                fg_color=theme.ACCENT, hover_color=theme.ACCENT_HOVER, width=150, height=26
            )
            btn_baixar.pack(side="right")

    def _on_atualizar_agora(self, download_url):
        from tkinter import messagebox
        confirmar = messagebox.askyesno(
            "Atualizar ACE Helper",
            "Isso vai baixar a nova versão, fechar o ACE Helper, trocar pelo "
            "arquivo novo, e reabrir automaticamente. Deseja continuar?"
        )
        if not confirmar:
            return

        self.btn_atualizar_agora.configure(state="disabled", text="Baixando...")

        thread = threading.Thread(target=self._run_self_update, args=(download_url,), daemon=True)
        thread.start()

    def _run_self_update(self, download_url):
        # Busca a URL de download de novo, na hora — em vez de confiar
        # só na que foi capturada quando o aviso apareceu (evita
        # problema se aquela consulta tiver vindo incompleta por
        # qualquer instabilidade pontual da API do GitHub).
        resultado_fresco = check_for_update(APP_VERSION)
        if resultado_fresco.get("download_url"):
            download_url = resultado_fresco["download_url"]

        if not download_url:
            self.after(0, lambda: self.update_label.configure(
                text="Não foi possível encontrar o .exe do release. Abrindo página do GitHub..."
            ))
            self.after(0, open_releases_page)
            self.after(0, lambda: self.btn_atualizar_agora.configure(state="normal", text="Atualizar agora"))
            return

        def progress_cb(baixado, total):
            pct = int((baixado / total) * 100) if total else 0
            self.after(0, lambda: self.update_label.configure(text=f"Baixando atualização... {pct}%"))

        sucesso, mensagem = self_update(download_url, progress_callback=progress_cb)

        if sucesso:
            self.after(0, lambda: self.update_label.configure(text=mensagem))
            self.after(1500, self.destroy)
        else:
            from tkinter import messagebox
            self.after(0, lambda: messagebox.showerror("Atualização falhou", mensagem))
            self.after(0, lambda: self.btn_atualizar_agora.configure(state="normal", text="Atualizar agora"))
