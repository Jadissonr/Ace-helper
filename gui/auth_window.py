"""
Tela de entrada do ACE Helper. Pede uma chave de acesso e valida
contra o Cloudflare Worker remoto (core/auth.py) antes de liberar a
abertura da janela principal. Roda a validação em thread separada pra
não travar a UI durante a chamada de rede.
"""

import os
import threading
import customtkinter as ctk
from PIL import Image

from core.auth import validate_key
from core.paths import resource_path

ACCENT_COLOR = "#a78bfa"
ACCENT_HOVER = "#8b6cf0"
BG_COLOR = "#0a0a0c"
ERROR_COLOR = "#f87171"

LOGO_PATH = resource_path("assets", "logo_transparent.png")
ICON_PATH = resource_path("assets", "icon.ico")


class AuthWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.authenticated = False

        ctk.set_appearance_mode("dark")

        self.title("ACE Helper — Acesso")
        self.geometry("380x300")
        self.resizable(False, False)
        self.configure(fg_color=BG_COLOR)

        if os.path.exists(ICON_PATH):
            try:
                self.iconbitmap(ICON_PATH)
            except Exception:
                pass

        self._build_ui()

    def _build_ui(self):
        if os.path.exists(LOGO_PATH):
            logo_pil = Image.open(LOGO_PATH)
            logo_w, logo_h = logo_pil.size
            target_h = 44
            target_w = int(logo_w * (target_h / logo_h))
            logo_image = ctk.CTkImage(light_image=logo_pil, dark_image=logo_pil, size=(target_w, target_h))
            logo_label = ctk.CTkLabel(self, image=logo_image, text="")
            logo_label.pack(pady=(28, 8))

        subtitle = ctk.CTkLabel(
            self, text="Digite sua chave de acesso para continuar",
            font=ctk.CTkFont(size=12), text_color="gray60"
        )
        subtitle.pack(pady=(0, 18))

        self.entry = ctk.CTkEntry(self, show="•", width=260, placeholder_text="Chave de acesso")
        self.entry.pack(pady=(0, 10))
        self.entry.bind("<Return>", lambda _e: self._on_entrar())
        self.entry.focus()

        self.status_label = ctk.CTkLabel(
            self, text="", font=ctk.CTkFont(size=11), text_color=ERROR_COLOR, wraplength=300
        )
        self.status_label.pack(pady=(0, 10))

        self.btn_entrar = ctk.CTkButton(
            self, text="Entrar", command=self._on_entrar,
            fg_color=ACCENT_COLOR, hover_color=ACCENT_HOVER, width=260
        )
        self.btn_entrar.pack()

    def _on_entrar(self):
        key = self.entry.get()
        self.btn_entrar.configure(state="disabled", text="Validando...")
        self.status_label.configure(text="")

        thread = threading.Thread(target=self._run_validate, args=(key,), daemon=True)
        thread.start()

    def _run_validate(self, key):
        valido, mensagem = validate_key(key)
        self.after(0, self._on_result, valido, mensagem)

    def _on_result(self, valido, mensagem):
        if valido:
            from core.auth import save_device_authorization
            save_device_authorization()
            self.authenticated = True
            self.destroy()
        else:
            self.status_label.configure(text=mensagem)
            self.btn_entrar.configure(state="normal", text="Entrar")
