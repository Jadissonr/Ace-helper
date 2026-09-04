"""
Aba "Debloat" — lista os apps UWP disponíveis para remoção, mostra se
cada um está instalado ou já removido, e permite remover/restaurar os
selecionados. Cria um ponto de restauração antes de qualquer ação,
igual o módulo de Tweaks. Visual em CustomTkinter.
"""

import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
import threading

from core.debloat import (
    load_debloat_list, remove_multiple, restore_multiple, is_installed,
    get_standard_apps
)
from core.restore_point import create_restore_point
from gui.scroll_fix import fix_scroll_ghosting
from gui.progress_widget import ProgressPanel
from gui import theme

ACCENT_COLOR = theme.ACCENT
ACCENT_HOVER = theme.ACCENT_HOVER
BADGE_COLOR = theme.ACCENT
REMOVED_COLOR = theme.SUCCESS


class DebloatTab(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self.vars = {}
        self.status_labels = {}
        self.apps = load_debloat_list()

        self._build_ui()
        self._refresh_status()

    def _build_ui(self):
        aviso = ctk.CTkLabel(
            self,
            text="Selecione os apps que deseja remover ou restaurar:",
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w"
        )
        aviso.pack(fill="x", padx=5, pady=(10, 0))

        standard_frame = ctk.CTkFrame(self, fg_color="transparent")
        standard_frame.pack(fill="x", padx=5, pady=(8, 0))

        self.btn_standard = ctk.CTkButton(
            standard_frame, text="⚡ Debloat Padrão", command=self._on_remover_padrao,
            fg_color=ACCENT_COLOR, hover_color=ACCENT_HOVER
        )
        self.btn_standard.pack(side="left")

        qtd_padrao = len(get_standard_apps(self.apps))
        standard_lbl = ctk.CTkLabel(
            standard_frame,
            text=f"Remove de uma vez os {qtd_padrao} apps mais comuns de serem descartados.",
            font=ctk.CTkFont(size=11), text_color="gray60"
        )
        standard_lbl.pack(side="left", padx=(10, 0))

        list_frame = ctk.CTkScrollableFrame(self, fg_color=theme.SURFACE)
        list_frame.pack(fill="both", expand=True, padx=5, pady=5)
        fix_scroll_ghosting(list_frame)

        for app in self.apps:
            row = ctk.CTkFrame(list_frame, fg_color="transparent")
            row.pack(fill="x", pady=3, padx=2)
            row.grid_columnconfigure(1, weight=1)

            var = tk.BooleanVar(value=False)
            self.vars[app["id"]] = var

            chk = ctk.CTkCheckBox(row, text="", variable=var, onvalue=True, offvalue=False, width=20)
            chk.grid(row=0, column=0, rowspan=2, sticky="n", padx=(4, 8), pady=2)

            nome_lbl = ctk.CTkLabel(row, text=app["nome"], font=ctk.CTkFont(size=12, weight="bold"), anchor="w")
            nome_lbl.grid(row=0, column=1, sticky="w")

            if app.get("standard", False):
                badge = ctk.CTkLabel(
                    row, text="PADRÃO", font=ctk.CTkFont(size=9, weight="bold"),
                    text_color="white", fg_color=BADGE_COLOR, corner_radius=4, padx=6
                )
                badge.grid(row=0, column=2, sticky="e", padx=(6, 6))

            desc_lbl = ctk.CTkLabel(
                row, text=app["descricao"], font=ctk.CTkFont(size=10),
                text_color="gray60", anchor="w", justify="left", wraplength=380
            )
            desc_lbl.grid(row=1, column=1, columnspan=2, sticky="w")

            status_lbl = ctk.CTkLabel(row, text="...", width=90, anchor="e", font=ctk.CTkFont(size=10))
            status_lbl.grid(row=0, column=3, rowspan=2, sticky="e", padx=(6, 4))
            self.status_labels[app["id"]] = status_lbl

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=8)

        self.btn_remover = ctk.CTkButton(btn_frame, text="Remover selecionados", command=self._on_remover)
        self.btn_remover.pack(side="left", padx=5)

        self.btn_restaurar = ctk.CTkButton(
            btn_frame, text="Restaurar selecionados", command=self._on_restaurar,
            fg_color="transparent", border_width=1
        )
        self.btn_restaurar.pack(side="left", padx=5)

        self.btn_atualizar = ctk.CTkButton(
            btn_frame, text="Atualizar status", command=self._refresh_status,
            fg_color="transparent", border_width=1
        )
        self.btn_atualizar.pack(side="left", padx=5)

        # Barra de progresso e log só aparecem quando uma ação é
        # disparada (ver _revelar_progresso_e_log).
        self.progress = ProgressPanel(self)
        self.log_box = ctk.CTkTextbox(self, height=130, state="disabled")

    def _revelar_progresso_e_log(self):
        """Mostra a barra de progresso e o log, se ainda não estiverem
        visíveis (chamado no início de qualquer ação)."""
        if not self.progress.winfo_ismapped():
            self.progress.pack(fill="x", padx=5, pady=(0, 8))
        if not self.log_box.winfo_ismapped():
            self.log_box.pack(fill="x", expand=False, padx=5, pady=(0, 10))

    def _append_log(self, text: str):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", text + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def _refresh_status(self):
        for app in self.apps:
            instalado = is_installed(app)
            lbl = self.status_labels[app["id"]]
            if instalado:
                lbl.configure(text="● Instalado", text_color="gray60")
            else:
                lbl.configure(text="○ Removido", text_color=REMOVED_COLOR)

    def _get_selecionados(self):
        return [a for a in self.apps if self.vars[a["id"]].get()]

    def _on_remover(self):
        self._executar_acao(remove_multiple, "Removendo")

    def _on_restaurar(self):
        self._executar_acao(restore_multiple, "Restaurando")

    def _on_remover_padrao(self):
        padrao = get_standard_apps(self.apps)
        nomes = "\n".join(f"• {a['nome']}" for a in padrao)

        confirmar = messagebox.askyesno(
            "Debloat Padrão",
            f"Isso vai remover {len(padrao)} apps considerados bloatware comum:\n\n{nomes}\n\nDeseja continuar?"
        )
        if not confirmar:
            return

        for app in self.apps:
            self.vars[app["id"]].set(app.get("standard", False))

        self.btn_standard.configure(state="disabled")
        self.btn_remover.configure(state="disabled")
        self.btn_restaurar.configure(state="disabled")
        self._revelar_progresso_e_log()
        self.progress.start_indeterminate("Preparando...")
        self._append_log(f"Removendo Debloat Padrão ({len(padrao)} apps)...")

        thread = threading.Thread(target=self._run_acao_padrao, args=(padrao,), daemon=True)
        thread.start()

    def _run_acao_padrao(self, padrao):
        self._criar_ponto_restauracao()

        total = len(padrao)
        completos = 0
        self.after(0, self.progress.start_determinate, total, f"Removendo 0/{total}...")

        def callback(nome, sucesso, mensagem):
            nonlocal completos
            completos += 1
            status = "OK" if sucesso else "ERRO"
            self.after(0, self._append_log, f"[{status}] {mensagem}")
            self.after(0, self.progress.step, completos, nome)

        remove_multiple(padrao, progress_callback=callback)

        self.after(0, self._append_log, "Debloat Padrão concluído.")
        self.after(0, self.progress.finish, f"Debloat Padrão concluído ({total}/{total}).")
        self.after(0, self._refresh_status)
        self.after(0, lambda: self.btn_standard.configure(state="normal"))
        self.after(0, lambda: self.btn_remover.configure(state="normal"))
        self.after(0, lambda: self.btn_restaurar.configure(state="normal"))

    def _criar_ponto_restauracao(self):
        self.after(0, self.progress.start_indeterminate, "Criando ponto de restauração...")
        self.after(0, self._append_log, "Criando ponto de restauração...")
        sucesso, mensagem = create_restore_point()
        status = "OK" if sucesso else "AVISO"
        self.after(0, self._append_log, f"[{status}] {mensagem}")

    def _executar_acao(self, funcao, verbo: str):
        selecionados = self._get_selecionados()
        if not selecionados:
            messagebox.showwarning("Nada selecionado", "Selecione ao menos um app.")
            return

        self.btn_remover.configure(state="disabled")
        self.btn_restaurar.configure(state="disabled")
        self._revelar_progresso_e_log()
        self.progress.start_indeterminate("Preparando...")
        self._append_log(f"{verbo} {len(selecionados)} app(s)...")

        thread = threading.Thread(target=self._run_acao, args=(funcao, selecionados), daemon=True)
        thread.start()

    def _run_acao(self, funcao, selecionados):
        self._criar_ponto_restauracao()

        total = len(selecionados)
        completos = 0
        self.after(0, self.progress.start_determinate, total, f"Processando 0/{total}...")

        def callback(nome, sucesso, mensagem):
            nonlocal completos
            completos += 1
            status = "OK" if sucesso else "ERRO"
            self.after(0, self._append_log, f"[{status}] {mensagem}")
            self.after(0, self.progress.step, completos, nome)

        funcao(selecionados, progress_callback=callback)

        self.after(0, self._append_log, "Concluído.")
        self.after(0, self.progress.finish, f"Concluído ({total}/{total}).")
        self.after(0, self._refresh_status)
        self.after(0, lambda: self.btn_remover.configure(state="normal"))
        self.after(0, lambda: self.btn_restaurar.configure(state="normal"))
