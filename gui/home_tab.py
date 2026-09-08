"""
Aba "Início" — painel resumido: estatísticas do sistema (CPU/RAM/Disco),
status geral (admin, GPU) e atalhos rápidos pras outras abas.
"""

import customtkinter as ctk

from core.system_stats import get_stats, is_admin, PSUTIL_AVAILABLE
from gui import theme

REFRESH_MS = 2000


class HomeTab(ctk.CTkFrame):
    def __init__(self, parent, on_navigate=None):
        super().__init__(parent, fg_color="transparent")
        self.on_navigate = on_navigate
        self._stat_bars = {}
        self._stat_labels = {}

        self._build_ui()
        self._refresh_stats()

    def _build_ui(self):
        # --- Boas-vindas ---
        header = ctk.CTkLabel(
            self, text="Painel Geral", font=theme.font_display(20),
            text_color=theme.TEXT_PRIMARY, anchor="w"
        )
        header.pack(fill="x", padx=5, pady=(10, 2))

        sub = ctk.CTkLabel(
            self, text="Visão rápida da máquina e atalhos pras ferramentas do ACE Helper.",
            font=theme.font_body(12), text_color=theme.TEXT_MUTED, anchor="w"
        )
        sub.pack(fill="x", padx=5, pady=(0, 14))

        # --- Cards de estatísticas ---
        stats_row = ctk.CTkFrame(self, fg_color="transparent")
        stats_row.pack(fill="x", padx=5, pady=(0, 14))
        for i in range(3):
            stats_row.grid_columnconfigure(i, weight=1)

        self._build_stat_card(stats_row, "cpu", "🔲 CPU", 0)
        self._build_stat_card(stats_row, "ram", "🧠 RAM", 1)
        self._build_stat_card(stats_row, "disk", "💾 Disco (C:)", 2)

        if not PSUTIL_AVAILABLE:
            warn = ctk.CTkLabel(
                self, text="Estatísticas indisponíveis nesse sistema.",
                font=theme.font_body(11), text_color=theme.WARNING
            )
            warn.pack(anchor="w", padx=5, pady=(0, 10))

        # --- Status geral ---
        status_card = theme.glow_card(self)
        status_card.pack(fill="x", padx=5, pady=(0, 14))
        status_inner = ctk.CTkFrame(status_card, fg_color="transparent")
        status_inner.pack(fill="x", padx=16, pady=14)

        ctk.CTkLabel(
            status_inner, text="STATUS", font=theme.font_heading(11),
            text_color=theme.ACCENT_2
        ).pack(anchor="w", pady=(0, 8))

        admin_ok = is_admin()
        admin_text = "✅ Rodando como Administrador" if admin_ok else "⚠️ Sem privilégios de Administrador"
        admin_color = theme.SUCCESS if admin_ok else theme.WARNING
        ctk.CTkLabel(
            status_inner, text=admin_text, font=theme.font_body(12), text_color=admin_color, anchor="w"
        ).pack(anchor="w", pady=2)

        # --- Atalhos rápidos ---
        shortcuts_title = ctk.CTkLabel(
            self, text="ATALHOS RÁPIDOS", font=theme.font_heading(11),
            text_color=theme.ACCENT_2, anchor="w"
        )
        shortcuts_title.pack(fill="x", padx=5, pady=(4, 8))

        shortcuts_row = ctk.CTkFrame(self, fg_color="transparent")
        shortcuts_row.pack(fill="x", padx=5)
        for i in range(5):
            shortcuts_row.grid_columnconfigure(i, weight=1)

        self._build_shortcut(shortcuts_row, "📦", "Instalar Apps", "Steam, Discord, navegadores e mais", "instalar", 0)
        self._build_shortcut(shortcuts_row, "⚡", "Tweaks", "Otimize performance e privacidade", "tweaks", 1)
        self._build_shortcut(shortcuts_row, "🌐", "Rede", "DNS, cache e teste de latência", "rede", 2)
        self._build_shortcut(shortcuts_row, "🚀", "Inicialização", "Gerencie programas de boot", "startup", 3)
        self._build_shortcut(shortcuts_row, "🧹", "Debloat", "Remova apps desnecessários do Windows", "debloat", 4)

    def _build_stat_card(self, parent, key, title, col):
        card = theme.glow_card(parent)
        card.grid(row=0, column=col, sticky="nsew", padx=6)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=14, pady=12)

        ctk.CTkLabel(
            inner, text=title, font=theme.font_body(11), text_color=theme.TEXT_MUTED, anchor="w"
        ).pack(anchor="w")

        value_lbl = ctk.CTkLabel(
            inner, text="--%", font=theme.font_mono(22, "bold"), text_color=theme.TEXT_PRIMARY, anchor="w"
        )
        value_lbl.pack(anchor="w", pady=(2, 6))
        self._stat_labels[key] = value_lbl

        bar = ctk.CTkProgressBar(inner, progress_color=theme.ACCENT, height=6)
        bar.pack(fill="x")
        bar.set(0)
        self._stat_bars[key] = bar

    def _build_shortcut(self, parent, icon, title, desc, nav_key, col):
        card = theme.glow_card(parent, fg_color=theme.SURFACE)
        card.grid(row=0, column=col, sticky="nsew", padx=6, pady=4)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=14, pady=14)

        ctk.CTkLabel(inner, text=icon, font=theme.font_display(22)).pack(anchor="w")
        ctk.CTkLabel(
            inner, text=title, font=theme.font_heading(13), text_color=theme.TEXT_PRIMARY, anchor="w"
        ).pack(anchor="w", pady=(6, 2))
        ctk.CTkLabel(
            inner, text=desc, font=theme.font_body(10), text_color=theme.TEXT_MUTED,
            anchor="w", justify="left", wraplength=160
        ).pack(anchor="w")

        def _go(_e=None):
            if self.on_navigate:
                self.on_navigate(nav_key)

        for widget in (card, inner):
            widget.bind("<Button-1>", _go)
            widget.configure(cursor="hand2")

    def _refresh_stats(self):
        stats = get_stats()

        self._update_stat("cpu", stats["cpu_percent"])
        self._update_stat("ram", stats["ram_percent"])
        self._update_stat("disk", stats["disk_percent"])

        self.after(REFRESH_MS, self._refresh_stats)

    def _update_stat(self, key, percent):
        if percent is None:
            self._stat_labels[key].configure(text="--%")
            self._stat_bars[key].set(0)
            return

        self._stat_labels[key].configure(text=f"{percent:.0f}%")
        self._stat_bars[key].set(percent / 100)

        if percent >= 85:
            cor = theme.ERROR
        elif percent >= 60:
            cor = theme.WARNING
        else:
            cor = theme.ACCENT
        self._stat_bars[key].configure(progress_color=cor)
