"""
Página "Rede" — ferramentas de otimização de conexão: limpar cache de
DNS, trocar servidor DNS, resetar pilha TCP/IP, e teste de latência.
"""

import threading
import customtkinter as ctk
from tkinter import messagebox

from core.network_tools import flush_dns, reset_tcpip, set_dns, restore_dns_dhcp, ping_test
from core.restore_point import create_restore_point
from gui.progress_widget import ProgressPanel
from gui import theme


class NetworkTab(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self._build_ui()

    def _build_ui(self):
        aviso = ctk.CTkLabel(
            self, text="Ferramentas de otimização de rede/conexão:",
            font=theme.font_heading(13), anchor="w"
        )
        aviso.pack(fill="x", padx=5, pady=(10, 14))

        # --- DNS ---
        dns_card = theme.glow_card(self, fg_color=theme.SURFACE_ALT)
        dns_card.pack(fill="x", padx=5, pady=(0, 10))
        dns_inner = ctk.CTkFrame(dns_card, fg_color="transparent")
        dns_inner.pack(fill="x", padx=16, pady=14)

        ctk.CTkLabel(
            dns_inner, text="🌐 Servidor DNS", font=theme.font_heading(12)
        ).pack(anchor="w")
        ctk.CTkLabel(
            dns_inner, text="Um DNS mais rápido pode reduzir a demora pra resolver endereços de sites e servidores de jogo.",
            font=theme.font_body(11), text_color=theme.TEXT_MUTED, anchor="w", justify="left", wraplength=520
        ).pack(anchor="w", pady=(2, 10))

        dns_btns = ctk.CTkFrame(dns_inner, fg_color="transparent")
        dns_btns.pack(fill="x")

        ctk.CTkButton(
            dns_btns, text="Usar Cloudflare (1.1.1.1)", command=lambda: self._on_set_dns("cloudflare"),
            fg_color=theme.ACCENT, hover_color=theme.ACCENT_HOVER, width=190
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            dns_btns, text="Usar Google (8.8.8.8)", command=lambda: self._on_set_dns("google"),
            fg_color=theme.ACCENT_2, hover_color=theme.ACCENT_2_HOVER, width=170
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            dns_btns, text="Restaurar Automático", command=self._on_restore_dns,
            fg_color="transparent", border_width=1, width=160
        ).pack(side="left")

        # --- Cache DNS + Reset TCP/IP ---
        maint_card = theme.glow_card(self, fg_color=theme.SURFACE_ALT)
        maint_card.pack(fill="x", padx=5, pady=(0, 10))
        maint_inner = ctk.CTkFrame(maint_card, fg_color="transparent")
        maint_inner.pack(fill="x", padx=16, pady=14)

        ctk.CTkLabel(
            maint_inner, text="🧹 Manutenção de Conexão", font=theme.font_heading(12)
        ).pack(anchor="w")
        ctk.CTkLabel(
            maint_inner,
            text="Limpar o cache de DNS resolve sites que pararam de carregar. "
                 "Resetar a pilha TCP/IP ajuda em problemas de conexão mais "
                 "teimosos (exige reiniciar o PC).",
            font=theme.font_body(11), text_color=theme.TEXT_MUTED, anchor="w", justify="left", wraplength=520
        ).pack(anchor="w", pady=(2, 10))

        maint_btns = ctk.CTkFrame(maint_inner, fg_color="transparent")
        maint_btns.pack(fill="x")

        ctk.CTkButton(
            maint_btns, text="Limpar Cache de DNS", command=self._on_flush_dns,
            fg_color=theme.ACCENT, hover_color=theme.ACCENT_HOVER, width=170
        ).pack(side="left", padx=(0, 8))

        self.btn_reset_tcpip = ctk.CTkButton(
            maint_btns, text="Resetar Pilha TCP/IP", command=self._on_reset_tcpip,
            fg_color="transparent", border_width=1, border_color=theme.WARNING,
            text_color=theme.WARNING, width=170
        )
        self.btn_reset_tcpip.pack(side="left")

        # --- Teste de latência ---
        ping_card = theme.glow_card(self, fg_color=theme.SURFACE_ALT)
        ping_card.pack(fill="x", padx=5, pady=(0, 10))
        ping_inner = ctk.CTkFrame(ping_card, fg_color="transparent")
        ping_inner.pack(fill="x", padx=16, pady=14)

        ping_header = ctk.CTkFrame(ping_inner, fg_color="transparent")
        ping_header.pack(fill="x")
        ctk.CTkLabel(
            ping_header, text="📶 Teste de Latência", font=theme.font_heading(12)
        ).pack(side="left")

        self.btn_ping = ctk.CTkButton(
            ping_header, text="Testar agora", command=self._on_ping_test,
            fg_color=theme.ACCENT, hover_color=theme.ACCENT_HOVER, width=120
        )
        self.btn_ping.pack(side="right")

        self.ping_results_frame = ctk.CTkFrame(ping_inner, fg_color="transparent")
        self.ping_results_frame.pack(fill="x", pady=(10, 0))
        self.ping_labels = {}

        # --- Progresso + log (só aparecem quando alguma ação roda) ---
        self.progress = ProgressPanel(self)
        self.log_box = ctk.CTkTextbox(self, height=120, state="disabled")

    def _revelar_progresso_e_log(self):
        if not self.progress.winfo_ismapped():
            self.progress.pack(fill="x", padx=5, pady=(0, 8))
        if not self.log_box.winfo_ismapped():
            self.log_box.pack(fill="x", expand=False, padx=5, pady=(0, 10))

    def _append_log(self, text: str):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", text + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    # --- DNS ---
    def _on_set_dns(self, provider):
        self._revelar_progresso_e_log()
        self.progress.start_indeterminate(f"Configurando DNS ({provider})...")
        self._append_log(f"Alterando DNS para {provider}...")
        thread = threading.Thread(target=self._run_dns_action, args=(set_dns, provider), daemon=True)
        thread.start()

    def _on_restore_dns(self):
        self._revelar_progresso_e_log()
        self.progress.start_indeterminate("Restaurando DNS automático...")
        self._append_log("Restaurando DNS automático...")
        thread = threading.Thread(target=self._run_dns_action, args=(restore_dns_dhcp, None), daemon=True)
        thread.start()

    def _run_dns_action(self, funcao, arg):
        sucesso, mensagem = funcao(arg) if arg else funcao()
        status = "OK" if sucesso else "ERRO"
        self.after(0, self._append_log, f"[{status}] {mensagem}")
        self.after(0, self.progress.finish, mensagem)

    # --- Cache DNS ---
    def _on_flush_dns(self):
        self._revelar_progresso_e_log()
        self.progress.start_indeterminate("Limpando cache de DNS...")
        self._append_log("Limpando cache de DNS...")
        thread = threading.Thread(target=self._run_flush_dns, daemon=True)
        thread.start()

    def _run_flush_dns(self):
        sucesso, mensagem = flush_dns()
        status = "OK" if sucesso else "ERRO"
        self.after(0, self._append_log, f"[{status}] {mensagem}")
        self.after(0, self.progress.finish, mensagem)

    # --- Reset TCP/IP ---
    def _on_reset_tcpip(self):
        confirmar = messagebox.askyesno(
            "Resetar pilha TCP/IP",
            "Isso vai resetar as configurações de rede do Windows (Winsock e "
            "pilha IP). É seguro, mas exige reiniciar o PC pra concluir.\n\n"
            "Um ponto de restauração será criado antes. Deseja continuar?"
        )
        if not confirmar:
            return

        self.btn_reset_tcpip.configure(state="disabled")
        self._revelar_progresso_e_log()
        self.progress.start_indeterminate("Preparando...")
        thread = threading.Thread(target=self._run_reset_tcpip, daemon=True)
        thread.start()

    def _run_reset_tcpip(self):
        self.after(0, self._append_log, "Criando ponto de restauração...")
        sucesso_rp, msg_rp = create_restore_point()
        status_rp = "OK" if sucesso_rp else "AVISO"
        self.after(0, self._append_log, f"[{status_rp}] {msg_rp}")

        self.after(0, self.progress.start_indeterminate, "Resetando pilha TCP/IP...")
        sucesso, mensagem = reset_tcpip()
        status = "OK" if sucesso else "ERRO"
        self.after(0, self._append_log, f"[{status}] {mensagem}")
        self.after(0, self.progress.finish, mensagem)
        self.after(0, lambda: self.btn_reset_tcpip.configure(state="normal"))

    # --- Teste de latência ---
    def _on_ping_test(self):
        self.btn_ping.configure(state="disabled", text="Testando...")
        for widget in self.ping_results_frame.winfo_children():
            widget.destroy()
        self.ping_labels = {}

        thread = threading.Thread(target=self._run_ping_test, daemon=True)
        thread.start()

    def _run_ping_test(self):
        resultados = ping_test()
        self.after(0, self._show_ping_results, resultados)

    def _show_ping_results(self, resultados):
        for nome, host, latencia in resultados:
            row = ctk.CTkFrame(self.ping_results_frame, fg_color="transparent")
            row.pack(fill="x", pady=2)

            ctk.CTkLabel(
                row, text=f"{nome} ({host})", font=theme.font_body(11),
                text_color=theme.TEXT_MUTED, anchor="w"
            ).pack(side="left")

            if latencia is None:
                texto, cor = "falhou", theme.ERROR
            elif latencia < 50:
                texto, cor = f"{latencia}ms", theme.SUCCESS
            elif latencia < 100:
                texto, cor = f"{latencia}ms", theme.WARNING
            else:
                texto, cor = f"{latencia}ms", theme.ERROR

            ctk.CTkLabel(
                row, text=texto, font=theme.font_mono(11, "bold"), text_color=cor, anchor="e"
            ).pack(side="right")

        self.btn_ping.configure(state="normal", text="Testar agora")
