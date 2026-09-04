"""
Aba "Tweaks" — lista os ajustes de registro disponíveis, mostra se cada
um já está aplicado (lendo o registro), e permite aplicar ou reverter
os selecionados. Roda em thread separada pra não travar a interface.
Visual em CustomTkinter. Também tem o painel de Plano de Energia.
"""

import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
import threading

from core.tweaks import (
    load_tweaks_list, apply_multiple, revert_multiple, is_applied,
    get_standard_tweaks, WINREG_AVAILABLE
)
from core.restore_point import create_restore_point
from core.power_plan import enable_ultimate_performance, restore_balanced_plan, get_active_plan_name
from core.wallpaper import set_ace_wallpaper
from core.nvidia_driver import check_for_update as check_nvidia_update, download_and_install as install_nvidia_driver
from gui.scroll_fix import fix_scroll_ghosting
from gui.progress_widget import ProgressPanel
from gui import theme

ACCENT_COLOR = theme.ACCENT
ACCENT_HOVER = theme.ACCENT_HOVER
BADGE_COLOR = theme.ACCENT
OK_COLOR = theme.SUCCESS


class TweaksTab(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self.vars = {}
        self.status_labels = {}
        self.tweaks = load_tweaks_list()
        self._nvidia_update_info = None

        self._build_ui()
        self._refresh_status()
        self._refresh_power_status()

    def _build_ui(self):
        aviso = ctk.CTkLabel(
            self,
            text="Selecione os ajustes que deseja aplicar ou reverter:",
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w"
        )
        aviso.pack(fill="x", padx=5, pady=(10, 0))

        if not WINREG_AVAILABLE:
            warn = ctk.CTkLabel(
                self,
                text="Aviso: este módulo só funciona no Windows (winreg não disponível neste sistema).",
                text_color="orange", anchor="w"
            )
            warn.pack(fill="x", padx=5, pady=(0, 5))

        standard_frame = ctk.CTkFrame(self, fg_color="transparent")
        standard_frame.pack(fill="x", padx=5, pady=(8, 0))

        self.btn_standard = ctk.CTkButton(
            standard_frame, text="⚡ Aplicar Tweak Padrão", command=self._on_aplicar_padrao,
            fg_color=ACCENT_COLOR, hover_color=ACCENT_HOVER
        )
        self.btn_standard.pack(side="left")

        qtd_padrao = len(get_standard_tweaks(self.tweaks))
        standard_lbl = ctk.CTkLabel(
            standard_frame,
            text=f"Aplica de uma vez os {qtd_padrao} ajustes recomendados e seguros.",
            font=ctk.CTkFont(size=11), text_color="gray60"
        )
        standard_lbl.pack(side="left", padx=(10, 0))

        power_frame = ctk.CTkFrame(self, fg_color=theme.SURFACE_ALT, corner_radius=10, border_width=1, border_color=theme.BORDER)
        power_frame.pack(fill="x", padx=5, pady=(10, 4))

        power_inner = ctk.CTkFrame(power_frame, fg_color="transparent")
        power_inner.pack(fill="x", padx=12, pady=10)

        power_title = ctk.CTkLabel(
            power_inner, text="⚙️ Plano de Energia", font=ctk.CTkFont(size=12, weight="bold")
        )
        power_title.pack(side="left")

        self.power_status_lbl = ctk.CTkLabel(
            power_inner, text="...", font=ctk.CTkFont(size=11), text_color="gray60"
        )
        self.power_status_lbl.pack(side="left", padx=(10, 0))

        self.btn_ultimate = ctk.CTkButton(
            power_inner, text="Ativar Ultimate Performance", command=self._on_ativar_ultimate,
            fg_color=ACCENT_COLOR, hover_color=ACCENT_HOVER, width=190
        )
        self.btn_ultimate.pack(side="right", padx=(6, 0))

        self.btn_balanceado = ctk.CTkButton(
            power_inner, text="Restaurar Balanceado", command=self._on_restaurar_balanceado,
            fg_color="transparent", border_width=1, width=170
        )
        self.btn_balanceado.pack(side="right")

        nvidia_frame = ctk.CTkFrame(self, fg_color=theme.SURFACE_ALT, corner_radius=10, border_width=1, border_color=theme.BORDER)
        nvidia_frame.pack(fill="x", padx=5, pady=(0, 4))

        nvidia_inner = ctk.CTkFrame(nvidia_frame, fg_color="transparent")
        nvidia_inner.pack(fill="x", padx=12, pady=10)

        nvidia_title = ctk.CTkLabel(
            nvidia_inner, text="🎮 Driver NVIDIA", font=ctk.CTkFont(size=12, weight="bold")
        )
        nvidia_title.pack(side="left")

        self.nvidia_status_lbl = ctk.CTkLabel(
            nvidia_inner, text="Clique em checar para ver a versão instalada.",
            font=ctk.CTkFont(size=11), text_color="gray60", wraplength=280, justify="left"
        )
        self.nvidia_status_lbl.pack(side="left", padx=(10, 0))

        self.btn_nvidia_atualizar = ctk.CTkButton(
            nvidia_inner, text="Atualizar driver", command=self._on_atualizar_nvidia,
            fg_color=ACCENT_COLOR, hover_color=ACCENT_HOVER, width=140, state="disabled"
        )
        self.btn_nvidia_atualizar.pack(side="right", padx=(6, 0))

        self.btn_nvidia_checar = ctk.CTkButton(
            nvidia_inner, text="Checar atualização", command=self._on_checar_nvidia,
            fg_color="transparent", border_width=1, width=150
        )
        self.btn_nvidia_checar.pack(side="right")

        list_frame = ctk.CTkScrollableFrame(self, fg_color=theme.SURFACE)
        list_frame.pack(fill="both", expand=True, padx=5, pady=5)
        fix_scroll_ghosting(list_frame)

        for tweak in self.tweaks:
            row = ctk.CTkFrame(list_frame, fg_color="transparent")
            row.pack(fill="x", pady=3, padx=2)
            row.grid_columnconfigure(1, weight=1)

            var = tk.BooleanVar(value=False)
            self.vars[tweak["id"]] = var

            chk = ctk.CTkCheckBox(row, text="", variable=var, onvalue=True, offvalue=False, width=20)
            chk.grid(row=0, column=0, rowspan=2, sticky="n", padx=(4, 8), pady=2)

            nome_lbl = ctk.CTkLabel(row, text=tweak["nome"], font=ctk.CTkFont(size=12, weight="bold"), anchor="w")
            nome_lbl.grid(row=0, column=1, sticky="w")

            if tweak.get("standard", False):
                badge = ctk.CTkLabel(
                    row, text="PADRÃO", font=ctk.CTkFont(size=9, weight="bold"),
                    text_color="white", fg_color=BADGE_COLOR, corner_radius=4, padx=6
                )
                badge.grid(row=0, column=2, sticky="e", padx=(6, 6))

            desc_lbl = ctk.CTkLabel(
                row, text=tweak["descricao"], font=ctk.CTkFont(size=10),
                text_color="gray60", anchor="w", justify="left", wraplength=380
            )
            desc_lbl.grid(row=1, column=1, columnspan=2, sticky="w")

            status_lbl = ctk.CTkLabel(row, text="...", width=80, anchor="e", font=ctk.CTkFont(size=10))
            status_lbl.grid(row=0, column=3, rowspan=2, sticky="e", padx=(6, 4))
            self.status_labels[tweak["id"]] = status_lbl

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=8)

        self.btn_aplicar = ctk.CTkButton(btn_frame, text="Aplicar selecionados", command=self._on_aplicar)
        self.btn_aplicar.pack(side="left", padx=5)

        self.btn_reverter = ctk.CTkButton(
            btn_frame, text="Reverter selecionados", command=self._on_reverter,
            fg_color="transparent", border_width=1
        )
        self.btn_reverter.pack(side="left", padx=5)

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

    def _refresh_power_status(self):
        if not WINREG_AVAILABLE:
            self.power_status_lbl.configure(text="indisponível")
            return
        nome = get_active_plan_name()
        self.power_status_lbl.configure(text=f"Ativo: {nome}" if nome else "não foi possível checar")

    def _on_ativar_ultimate(self):
        if not WINREG_AVAILABLE:
            messagebox.showerror("Indisponível", "Este módulo só funciona rodando no Windows.")
            return

        self.btn_ultimate.configure(state="disabled")
        self.btn_balanceado.configure(state="disabled")
        self._revelar_progresso_e_log()
        self.progress.start_indeterminate("Ativando Ultimate Performance...")
        self._append_log("Ativando plano Ultimate Performance...")

        thread = threading.Thread(target=self._run_power_action, args=(enable_ultimate_performance,), daemon=True)
        thread.start()

    def _on_restaurar_balanceado(self):
        if not WINREG_AVAILABLE:
            messagebox.showerror("Indisponível", "Este módulo só funciona rodando no Windows.")
            return

        self.btn_ultimate.configure(state="disabled")
        self.btn_balanceado.configure(state="disabled")
        self._revelar_progresso_e_log()
        self.progress.start_indeterminate("Restaurando plano Balanceado...")
        self._append_log("Restaurando plano Balanceado...")

        thread = threading.Thread(target=self._run_power_action, args=(restore_balanced_plan,), daemon=True)
        thread.start()

    def _run_power_action(self, funcao):
        sucesso, mensagem = funcao()
        status = "OK" if sucesso else "ERRO"
        self.after(0, self._append_log, f"[{status}] {mensagem}")
        self.after(0, self.progress.finish, mensagem)
        self.after(0, self._refresh_power_status)
        self.after(0, lambda: self.btn_ultimate.configure(state="normal"))
        self.after(0, lambda: self.btn_balanceado.configure(state="normal"))

    def _on_checar_nvidia(self):
        self.btn_nvidia_checar.configure(state="disabled", text="Checando...")
        self.btn_nvidia_atualizar.configure(state="disabled")
        self._revelar_progresso_e_log()
        self.progress.start_indeterminate("Checando driver da NVIDIA...")
        self._append_log("Checando versão do driver NVIDIA...")

        thread = threading.Thread(target=self._run_checar_nvidia, daemon=True)
        thread.start()

    def _run_checar_nvidia(self):
        info = check_nvidia_update()
        self._nvidia_update_info = info

        if info.get("error"):
            self.after(0, self._append_log, f"[AVISO] {info['error']}")
            self.after(0, lambda: self.nvidia_status_lbl.configure(text=info["error"]))
            self.after(0, self.progress.finish, "Não foi possível checar o driver.")
        else:
            gpu = info["gpu_name"]
            atual = info["current_version"]
            mais_recente = info["latest_version"]
            if info["has_update"]:
                texto = f"{gpu}: v{atual} instalada → v{mais_recente} disponível"
                self.after(0, lambda: self.btn_nvidia_atualizar.configure(state="normal"))
            else:
                texto = f"{gpu}: v{atual} já é a versão mais recente."
            self.after(0, self._append_log, texto)
            self.after(0, lambda: self.nvidia_status_lbl.configure(text=texto))
            self.after(0, self.progress.finish, texto)

        self.after(0, lambda: self.btn_nvidia_checar.configure(state="normal", text="Checar atualização"))

    def _on_atualizar_nvidia(self):
        info = self._nvidia_update_info
        if not info or info.get("error") or not info.get("has_update"):
            messagebox.showwarning("Nada pra atualizar", "Checa a atualização de novo antes de instalar.")
            return

        confirmar = messagebox.askyesno(
            "Atualizar driver NVIDIA",
            f"Isso vai baixar e instalar o driver NVIDIA v{info['latest_version']} "
            f"(atual: v{info['current_version']}) silenciosamente, sem abrir o "
            f"instalador na tela.\n\n"
            "Atualizar driver de GPU raramente dá problema, mas pode acontecer. "
            "Um ponto de restauração será criado antes, por segurança. Pode ser "
            "necessário reiniciar o PC ao final.\n\nDeseja continuar?"
        )
        if not confirmar:
            return

        self.btn_nvidia_checar.configure(state="disabled")
        self.btn_nvidia_atualizar.configure(state="disabled", text="Atualizando...")
        self._revelar_progresso_e_log()
        self._append_log(f"Iniciando atualização do driver NVIDIA para v{info['latest_version']}...")

        thread = threading.Thread(target=self._run_atualizar_nvidia, args=(info,), daemon=True)
        thread.start()

    def _run_atualizar_nvidia(self, info):
        self._criar_ponto_restauracao()

        self.after(0, self.progress.start_determinate, 100, "Baixando driver NVIDIA...")

        def progress_cb(baixado, total):
            pct = int((baixado / total) * 100) if total else 0
            self.after(0, self.progress.step, pct, f"Baixando driver ({pct}%)")

        sucesso, mensagem = install_nvidia_driver(info["download_url"], progress_callback=progress_cb)
        status = "OK" if sucesso else "ERRO"
        self.after(0, self._append_log, f"[{status}] {mensagem}")
        self.after(0, self.progress.finish, mensagem)
        self.after(0, lambda: self.nvidia_status_lbl.configure(text=mensagem))
        self.after(0, lambda: self.btn_nvidia_checar.configure(state="normal"))
        self.after(0, lambda: self.btn_nvidia_atualizar.configure(state="normal", text="Atualizar driver"))

    def _refresh_status(self):
        if not WINREG_AVAILABLE:
            for tweak in self.tweaks:
                self.status_labels[tweak["id"]].configure(text="indisponível")
            return

        for tweak in self.tweaks:
            aplicado = is_applied(tweak)
            lbl = self.status_labels[tweak["id"]]
            if aplicado:
                lbl.configure(text="● Aplicado", text_color=OK_COLOR)
            else:
                lbl.configure(text="○ Padrão", text_color="gray60")

    def _get_selecionados(self):
        return [t for t in self.tweaks if self.vars[t["id"]].get()]

    def _on_aplicar(self):
        self._executar_acao(apply_multiple, "Aplicando")

    def _on_reverter(self):
        self._executar_acao(revert_multiple, "Revertendo")

    def _on_aplicar_padrao(self):
        if not WINREG_AVAILABLE:
            messagebox.showerror("Indisponível", "Este módulo só funciona rodando no Windows.")
            return

        padrao = get_standard_tweaks(self.tweaks)
        nomes = "\n".join(f"• {t['nome']}" for t in padrao)

        confirmar = messagebox.askyesno(
            "Aplicar Tweak Padrão",
            f"Isso vai aplicar {len(padrao)} ajustes recomendados de uma vez:\n\n{nomes}\n\nDeseja continuar?"
        )
        if not confirmar:
            return

        for tweak in self.tweaks:
            self.vars[tweak["id"]].set(tweak.get("standard", False))

        self.btn_standard.configure(state="disabled")
        self.btn_aplicar.configure(state="disabled")
        self.btn_reverter.configure(state="disabled")
        self._revelar_progresso_e_log()
        self.progress.start_indeterminate("Preparando...")
        self._append_log(f"Aplicando Tweak Padrão ({len(padrao)} ajustes)...")

        thread = threading.Thread(target=self._run_acao_padrao, args=(padrao,), daemon=True)
        thread.start()

    def _run_acao_padrao(self, padrao):
        self._criar_ponto_restauracao()

        total = len(padrao)
        completos = 0
        self.after(0, self.progress.start_determinate, total, f"Aplicando 0/{total}...")

        def callback(nome, sucesso, mensagem):
            nonlocal completos
            completos += 1
            status = "OK" if sucesso else "ERRO"
            self.after(0, self._append_log, f"[{status}] {mensagem}")
            self.after(0, self.progress.step, completos, nome)

        apply_multiple(padrao, progress_callback=callback)
        self._aplicar_wallpaper()

        self.after(0, self._append_log, "Tweak Padrão concluído.")
        self.after(0, self.progress.finish, f"Tweak Padrão concluído ({total}/{total}).")
        self.after(0, self._refresh_status)
        self.after(0, lambda: self.btn_standard.configure(state="normal"))
        self.after(0, lambda: self.btn_aplicar.configure(state="normal"))
        self.after(0, lambda: self.btn_reverter.configure(state="normal"))

    def _aplicar_wallpaper(self):
        """Define o papel de parede da ACE depois de aplicar tweaks
        (não é chamado ao reverter)."""
        sucesso, mensagem = set_ace_wallpaper()
        status = "OK" if sucesso else "AVISO"
        self.after(0, self._append_log, f"[{status}] {mensagem}")

    def _criar_ponto_restauracao(self):
        """Cria um ponto de restauração do Windows antes de qualquer
        tweak ser aplicado/revertido. Roda dentro da thread de trabalho
        (pode levar alguns segundos) e nunca bloqueia a ação principal
        — se falhar, só avisa no log e segue em frente."""
        self.after(0, self.progress.start_indeterminate, "Criando ponto de restauração...")
        self.after(0, self._append_log, "Criando ponto de restauração...")
        sucesso, mensagem = create_restore_point()
        status = "OK" if sucesso else "AVISO"
        self.after(0, self._append_log, f"[{status}] {mensagem}")

    def _executar_acao(self, funcao, verbo: str):
        if not WINREG_AVAILABLE:
            messagebox.showerror("Indisponível", "Este módulo só funciona rodando no Windows.")
            return

        selecionados = self._get_selecionados()
        if not selecionados:
            messagebox.showwarning("Nada selecionado", "Selecione ao menos um tweak.")
            return

        self.btn_aplicar.configure(state="disabled")
        self.btn_reverter.configure(state="disabled")
        self._revelar_progresso_e_log()
        self.progress.start_indeterminate("Preparando...")
        self._append_log(f"{verbo} {len(selecionados)} tweak(s)...")

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

        if funcao is apply_multiple:
            self._aplicar_wallpaper()

        self.after(0, self._append_log, "Concluído.")
        self.after(0, self.progress.finish, f"Concluído ({total}/{total}).")
        self.after(0, self._refresh_status)
        self.after(0, lambda: self.btn_aplicar.configure(state="normal"))
        self.after(0, lambda: self.btn_reverter.configure(state="normal"))
