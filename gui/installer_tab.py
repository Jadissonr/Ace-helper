"""
Aba "Instalar Apps" — mostra plataformas/apps disponíveis via winget,
organizados em SEÇÕES por categoria (Plataformas de Jogos, Navegadores,
Utilitários), cada uma em formato de grade (cards com ícone, nome e
categoria). Clicar em qualquer parte do card ou no checkbox seleciona
o item. Instala os selecionados em thread separada.
"""

import os
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
import threading
from collections import OrderedDict

from core.installer import load_games_list, install_multiple, is_winget_available, upgrade_all
from core.paths import resource_path

ACCENT_COLOR = "#a78bfa"
ACCENT_HOVER = "#8b6cf0"
CARD_COLOR = "#1e1e21"
CARD_SELECTED_COLOR = "#2a2433"

COLUMNS = 3
CARD_WIDTH = 180
CARD_HEIGHT = 150

# Ordem fixa de exibição das seções
CATEGORIA_ORDEM = ["Plataformas de Jogos", "Navegadores", "Utilitários"]


class InstallerTab(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self.vars = {}
        self.games = load_games_list()

        self._build_ui()

    def _agrupar_por_categoria(self):
        grupos = OrderedDict((cat, []) for cat in CATEGORIA_ORDEM)
        for item in self.games:
            grupos.setdefault(item["categoria"], []).append(item)
        return grupos

    def _build_ui(self):
        aviso = ctk.CTkLabel(
            self,
            text="Selecione as plataformas e apps que deseja instalar:",
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w"
        )
        aviso.pack(fill="x", padx=5, pady=(10, 5))

        scroll_frame = ctk.CTkScrollableFrame(self, fg_color="#151517")
        scroll_frame.pack(fill="both", expand=True, padx=5, pady=5)

        grupos = self._agrupar_por_categoria()
        for categoria, itens in grupos.items():
            if not itens:
                continue
            self._build_secao(scroll_frame, categoria, itens)

        self.btn_instalar = ctk.CTkButton(
            self, text="Instalar selecionados", command=self._on_instalar,
            fg_color=ACCENT_COLOR, hover_color=ACCENT_HOVER
        )
        self.btn_instalar.pack(pady=10)

        self.btn_atualizar_tudo = ctk.CTkButton(
            self, text="🔄 Atualizar tudo", command=self._on_atualizar_tudo,
            fg_color="transparent", border_width=1
        )
        self.btn_atualizar_tudo.pack(pady=(0, 10))

        self.log_box = ctk.CTkTextbox(self, height=140, state="disabled")
        self.log_box.pack(fill="both", expand=True, padx=5, pady=(0, 10))

    def _build_secao(self, parent, categoria, itens):
        secao_frame = ctk.CTkFrame(parent, fg_color="transparent")
        secao_frame.pack(fill="x", padx=4, pady=(6, 2))

        titulo = ctk.CTkLabel(
            secao_frame, text=categoria, font=ctk.CTkFont(size=13, weight="bold"),
            text_color=ACCENT_COLOR, anchor="w"
        )
        titulo.pack(anchor="w", pady=(4, 6))

        grid_frame = ctk.CTkFrame(secao_frame, fg_color="transparent")
        grid_frame.pack(fill="x")
        for col in range(COLUMNS):
            grid_frame.grid_columnconfigure(col, weight=1)

        for idx, item in enumerate(itens):
            row, col = divmod(idx, COLUMNS)
            self._build_card(grid_frame, item, row, col)

    def _build_card(self, parent, item, row, col):
        card = ctk.CTkFrame(
            parent, fg_color=CARD_COLOR, corner_radius=10,
            border_width=2, border_color=CARD_COLOR,
            width=CARD_WIDTH, height=CARD_HEIGHT
        )
        card.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")
        card.grid_propagate(False)

        var = tk.BooleanVar(value=False)
        self.vars[item["winget_id"]] = var

        icon_path = resource_path("assets", "app_icons", f"{item['id']}.png")
        clickable_widgets = [card]

        if os.path.exists(icon_path):
            from PIL import Image
            icon_img = ctk.CTkImage(
                light_image=Image.open(icon_path), dark_image=Image.open(icon_path),
                size=(44, 44)
            )
            icon_lbl = ctk.CTkLabel(card, image=icon_img, text="")
            icon_lbl.pack(pady=(16, 6))
            clickable_widgets.append(icon_lbl)

        name_lbl = ctk.CTkLabel(
            card, text=item["nome"], font=ctk.CTkFont(size=12, weight="bold"),
            wraplength=CARD_WIDTH - 20, justify="center"
        )
        name_lbl.pack(padx=6)
        clickable_widgets.append(name_lbl)

        chk = ctk.CTkCheckBox(card, text="", variable=var, onvalue=True, offvalue=False, width=18, height=18)
        chk.place(relx=1.0, rely=0.0, x=-8, y=8, anchor="ne")

        def _update_style(*_args):
            if var.get():
                card.configure(border_color=ACCENT_COLOR, fg_color=CARD_SELECTED_COLOR)
            else:
                card.configure(border_color=CARD_COLOR, fg_color=CARD_COLOR)

        var.trace_add("write", _update_style)

        def _toggle(_event):
            var.set(not var.get())

        for widget in clickable_widgets:
            widget.bind("<Button-1>", _toggle)

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

    def _on_atualizar_tudo(self):
        if not is_winget_available():
            messagebox.showerror(
                "winget não encontrado",
                "O winget não está disponível neste sistema."
            )
            return

        confirmar = messagebox.askyesno(
            "Atualizar tudo",
            "Isso vai atualizar TODOS os aplicativos instalados via winget no "
            "seu sistema para a versão mais recente — não só os listados aqui "
            "no ACE Helper, mas qualquer app que você tenha instalado pelo "
            "winget (inclusive antes de usar o ACE Helper).\n\n"
            "Pode levar vários minutos dependendo de quantos apps precisarem "
            "de atualização. Deseja continuar?"
        )
        if not confirmar:
            return

        self.btn_instalar.configure(state="disabled")
        self.btn_atualizar_tudo.configure(state="disabled", text="Atualizando...")
        self._append_log("Iniciando atualização de todos os apps via winget (pode demorar)...")

        thread = threading.Thread(target=self._run_atualizar_tudo, daemon=True)
        thread.start()

    def _run_atualizar_tudo(self):
        sucesso, mensagem = upgrade_all()
        status = "OK" if sucesso else "ERRO"
        self.after(0, self._append_log, f"[{status}] {mensagem}")
        self.after(0, self._append_log, "Atualização finalizada.")
        self.after(0, lambda: self.btn_instalar.configure(state="normal"))
        self.after(0, lambda: self.btn_atualizar_tudo.configure(state="normal", text="🔄 Atualizar tudo"))
