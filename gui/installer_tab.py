"""
Aba "Instalar Jogos" — lista plataformas/launchers disponíveis via winget
com checkbox, e instala os selecionados em uma thread separada (pra não
travar a interface). Visual em CustomTkinter.
"""

import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
import threading

from core.installer import load_games_list, install_multiple, is_winget_available

ACCENT_COLOR = "#a78bfa"
ACCENT_HOVER = "#8b6cf0"


class InstallerTab(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self.vars = {}
        self.games = load_games_list()

        self._build_ui()

    def _build_ui(self):
        aviso = ctk.CTkLabel(
            self,
            text="Selecione as plataformas/jogos que deseja instalar:",
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w"
        )
        aviso.pack(fill="x", padx=5, pady=(10, 5))

        list_frame = ctk.CTkScrollableFrame(self, fg_color="#151517")
        list_frame.pack(fill="both", expand=True, padx=5, pady=5)

        for item in self.games:
            var = tk.BooleanVar(value=False)
            self.vars[item["winget_id"]] = var

            chk = ctk.CTkCheckBox(
                list_frame,
                text=f'{item["nome"]}  ·  {item["categoria"]}',
                variable=var, onvalue=True, offvalue=False,
                checkbox_width=20, checkbox_height=20
            )
            chk.pack(anchor="w", pady=4, padx=8)

        self.btn_instalar = ctk.CTkButton(
            self, text="Instalar selecionados", command=self._on_instalar,
            fg_color=ACCENT_COLOR, hover_color=ACCENT_HOVER
        )
        self.btn_instalar.pack(pady=10)

        self.log_box = ctk.CTkTextbox(self, height=160, state="disabled")
        self.log_box.pack(fill="both", expand=True, padx=5, pady=(0, 10))

    def _append_log(self, text: str):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", text + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def _on_instalar(self):
        if not is_winget_available():
            messagebox.showerror(
                "winget não encontrado",
                "O winget não está disponível neste sistema. "
                "Atualize o 'App Installer' pela Microsoft Store e tente novamente."
            )
            return

        selecionados = [
            item for item in self.games if self.vars[item["winget_id"]].get()
        ]

        if not selecionados:
            messagebox.showwarning("Nada selecionado", "Selecione ao menos um item para instalar.")
            return

        self.btn_instalar.configure(state="disabled", text="Instalando...")
        self._append_log(f"Iniciando instalação de {len(selecionados)} item(ns)...")

        thread = threading.Thread(target=self._run_install, args=(selecionados,), daemon=True)
        thread.start()

    def _run_install(self, selecionados):
        def callback(nome, sucesso, mensagem):
            status = "OK" if sucesso else "ERRO"
            self.after(0, self._append_log, f"[{status}] {mensagem}")

        install_multiple(selecionados, progress_callback=callback)

        self.after(0, self._append_log, "Instalação concluída.")
        self.after(0, lambda: self.btn_instalar.configure(state="normal", text="Instalar selecionados"))
