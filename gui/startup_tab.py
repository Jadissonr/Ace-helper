"""
Página "Inicialização" — lista os programas que abrem sozinhos com o
Windows e permite ativar/desativar cada um com um interruptor.
"""

import threading
import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox

from core.startup_manager import list_startup_items, set_item_enabled, WINREG_AVAILABLE
from gui.scroll_fix import fix_scroll_ghosting
from gui import theme


class StartupTab(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self.switch_vars = {}
        self.items = []

        self._build_ui()
        self._load_items()

    def _build_ui(self):
        header_row = ctk.CTkFrame(self, fg_color="transparent")
        header_row.pack(fill="x", padx=5, pady=(10, 4))

        ctk.CTkLabel(
            header_row, text="Programas que abrem junto com o Windows:",
            font=theme.font_heading(13), anchor="w"
        ).pack(side="left")

        self.btn_atualizar = ctk.CTkButton(
            header_row, text="🔄 Atualizar lista", command=self._load_items,
            fg_color="transparent", border_width=1, width=140, height=28
        )
        self.btn_atualizar.pack(side="right")

        if not WINREG_AVAILABLE:
            ctk.CTkLabel(
                self, text="Este recurso só funciona no Windows.",
                text_color=theme.WARNING, anchor="w"
            ).pack(fill="x", padx=5, pady=(0, 8))

        self.list_frame = ctk.CTkScrollableFrame(self, fg_color=theme.SURFACE)
        self.list_frame.pack(fill="both", expand=True, padx=5, pady=5)
        fix_scroll_ghosting(self.list_frame)

        self.empty_label = ctk.CTkLabel(
            self.list_frame, text="Carregando...", text_color=theme.TEXT_MUTED
        )
        self.empty_label.pack(pady=30)

        self.log_box = ctk.CTkTextbox(self, height=100, state="disabled")

    def _revelar_log(self):
        if not self.log_box.winfo_ismapped():
            self.log_box.pack(fill="x", expand=False, padx=5, pady=(0, 10))

    def _append_log(self, text: str):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", text + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def _load_items(self):
        self.btn_atualizar.configure(state="disabled", text="Carregando...")
        for widget in self.list_frame.winfo_children():
            widget.destroy()
        self.switch_vars = {}

        thread = threading.Thread(target=self._run_load_items, daemon=True)
        thread.start()

    def _run_load_items(self):
        items = list_startup_items()
        self.after(0, self._show_items, items)

    def _show_items(self, items):
        self.items = items
        self.btn_atualizar.configure(state="normal", text="🔄 Atualizar lista")

        for widget in self.list_frame.winfo_children():
            widget.destroy()

        if not items:
            msg = "Nenhum item de inicialização encontrado." if WINREG_AVAILABLE else "Indisponível fora do Windows."
            ctk.CTkLabel(self.list_frame, text=msg, text_color=theme.TEXT_MUTED).pack(pady=30)
            return

        # Ordena: habilitados primeiro, depois por nome
        items_ordenados = sorted(items, key=lambda i: (not i["enabled"], i["nome"].lower()))

        for item in items_ordenados:
            self._build_row(item)

    def _build_row(self, item):
        row = ctk.CTkFrame(self.list_frame, fg_color="transparent")
        row.pack(fill="x", pady=3, padx=2)
        row.grid_columnconfigure(1, weight=1)

        var = tk.BooleanVar(value=item["enabled"])
        self.switch_vars[item["id"]] = var

        switch = ctk.CTkSwitch(
            row, text="", variable=var, onvalue=True, offvalue=False,
            progress_color=theme.ACCENT, width=40,
            command=lambda it=item, v=var: self._on_toggle(it, v)
        )
        switch.grid(row=0, column=0, rowspan=2, sticky="n", padx=(4, 10), pady=2)

        nome_lbl = ctk.CTkLabel(
            row, text=item["nome"], font=theme.font_body(12, "bold"), anchor="w"
        )
        nome_lbl.grid(row=0, column=1, sticky="w")

        badge = ctk.CTkLabel(
            row, text=item["tipo"].upper(), font=theme.font_body(8, "bold"),
            text_color="white", fg_color=theme.ACCENT_2 if item["tipo"] == "atalho" else theme.ACCENT,
            corner_radius=4, padx=6
        )
        badge.grid(row=0, column=2, sticky="e", padx=(6, 6))

        local_lbl = ctk.CTkLabel(
            row, text=item["local"], font=theme.font_body(9),
            text_color=theme.TEXT_DIM, anchor="e"
        )
        local_lbl.grid(row=0, column=3, sticky="e", padx=(0, 4))

        caminho_lbl = ctk.CTkLabel(
            row, text=item["caminho"], font=theme.font_body(9),
            text_color=theme.TEXT_MUTED, anchor="w", wraplength=520, justify="left"
        )
        caminho_lbl.grid(row=1, column=1, columnspan=3, sticky="w")

    def _on_toggle(self, item, var):
        enabled = var.get()
        self._revelar_log()
        self._append_log(f"{'Habilitando' if enabled else 'Desabilitando'} {item['nome']}...")

        thread = threading.Thread(target=self._run_toggle, args=(item, enabled, var), daemon=True)
        thread.start()

    def _run_toggle(self, item, enabled, var):
        sucesso, mensagem = set_item_enabled(item, enabled)
        status = "OK" if sucesso else "ERRO"
        self.after(0, self._append_log, f"[{status}] {mensagem}")
        if not sucesso:
            # reverte o interruptor visualmente se a mudança falhou
            self.after(0, lambda: var.set(not enabled))
