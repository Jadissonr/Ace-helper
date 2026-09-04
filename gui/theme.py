"""
Paleta e constantes visuais centralizadas do ACE Helper — tema
"gamer/neon": fundo bem escuro, roxo como acento principal, ciano como
acento secundário (contraste "tech"), bordas com efeito de brilho
simulado (já que CTk não suporta sombra/glow de verdade).

Importar daqui em vez de repetir hex codes espalhados pelos arquivos.
"""

import customtkinter as ctk

# --- Cores base ---
BG = "#08080a"                 # fundo da janela, mais escuro que antes
SURFACE = "#131316"            # cards, painéis
SURFACE_ALT = "#1c1c20"        # cards em hover/destaque
BORDER = "#26262c"             # borda sutil padrão

# --- Acentos ---
ACCENT = "#a78bfa"             # roxo — ação primária
ACCENT_HOVER = "#8b6cf0"
ACCENT_GLOW = "#c4b5fd"        # roxo mais claro, usado em bordas de destaque
ACCENT_2 = "#22d3ee"           # ciano — contraste "tech", usado com moderação
ACCENT_2_HOVER = "#0ea5c4"

# --- Semânticas ---
SUCCESS = "#22c55e"
WARNING = "#f59e0b"
ERROR = "#f87171"

# --- Texto ---
TEXT_PRIMARY = "#f4f4f5"
TEXT_MUTED = "#8b8b93"
TEXT_DIM = "#5a5a62"

# --- Fontes (helpers) ---
def font_display(size=24, weight="bold"):
    return ctk.CTkFont(size=size, weight=weight)


def font_heading(size=14, weight="bold"):
    return ctk.CTkFont(size=size, weight=weight)


def font_body(size=12, weight="normal"):
    return ctk.CTkFont(size=size, weight=weight)


def font_mono(size=12, weight="normal"):
    # usado em números/estatísticas, pra reforçar o clima "tech"
    return ctk.CTkFont(family="Consolas", size=size, weight=weight)


def glow_card(parent, **kwargs):
    """Cria um CTkFrame estilo 'card com brilho sutil' — usa uma
    borda na cor de destaque em vez de sombra (CTk não tem sombra)."""
    defaults = dict(
        fg_color=SURFACE,
        corner_radius=12,
        border_width=1,
        border_color=BORDER,
    )
    defaults.update(kwargs)
    return ctk.CTkFrame(parent, **defaults)
