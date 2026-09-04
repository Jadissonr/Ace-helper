"""
Componente reutilizável de barra de progresso + texto de status, usado
nas 3 abas (Instalar Apps, Tweaks, Debloat) pra mostrar em qual etapa
de uma ação em lote (instalação, aplicação de tweaks, remoção de apps)
o app está no momento.

Dois modos:
- determinado: quando sabemos quantos itens tem no total (ex: instalar
  5 apps selecionados) — a barra avança item por item.
- indeterminado: quando não dá pra saber o progresso exato (ex: rodando
  um único comando do winget/powershell que não reporta etapas) — a
  barra fica animada até a ação terminar.
"""

import customtkinter as ctk

ACCENT_COLOR = "#a78bfa"


class ProgressPanel(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self._total = 0

        self.label = ctk.CTkLabel(
            self, text="", font=ctk.CTkFont(size=11), text_color="gray60", anchor="w"
        )
        self.label.pack(fill="x", padx=2)

        self.bar = ctk.CTkProgressBar(self, progress_color=ACCENT_COLOR)
        self.bar.pack(fill="x", padx=2, pady=(4, 0))
        self.bar.set(0)

    def start_determinate(self, total: int, text: str = ""):
        """Inicia o acompanhamento de uma ação com número de itens conhecido."""
        self._total = max(total, 1)
        try:
            self.bar.stop()
        except Exception:
            pass
        self.bar.configure(mode="determinate")
        self.bar.set(0)
        self.label.configure(text=text)

    def step(self, completed: int, item_name: str = ""):
        """Atualiza a barra pra refletir quantos itens já foram processados."""
        fracao = completed / self._total
        self.bar.set(fracao)
        if item_name:
            self.label.configure(text=f"{completed}/{self._total} — {item_name}")

    def start_indeterminate(self, text: str = ""):
        """Inicia uma animação de progresso sem total conhecido (ex: um
        único comando externo que não reporta etapas)."""
        self.bar.configure(mode="indeterminate")
        self.bar.start()
        self.label.configure(text=text)

    def finish(self, text: str = "Concluído"):
        """Marca a barra como concluída (100%) e para qualquer animação."""
        try:
            self.bar.stop()
        except Exception:
            pass
        self.bar.configure(mode="determinate")
        self.bar.set(1.0)
        self.label.configure(text=text)

    def reset(self):
        """Zera a barra e limpa o texto (ex: antes de uma nova ação)."""
        try:
            self.bar.stop()
        except Exception:
            pass
        self.bar.configure(mode="determinate")
        self.bar.set(0)
        self.label.configure(text="")
