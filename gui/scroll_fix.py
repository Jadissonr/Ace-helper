"""
Mitigação para um bug conhecido (e ainda não corrigido oficialmente)
do CustomTkinter: rolar um CTkScrollableFrame rápido demais faz a tela
"duplicar" o conteúdo por uma fração de segundo (rastro fantasma).

Issue oficial: https://github.com/TomSchimansky/CustomTkinter/issues/1510

Isso força um redesenho síncrono da tela logo após cada evento de
rolagem, em vez de deixar os redesenhos se acumularem — reduz bastante
o efeito, mas por ser um bug da própria biblioteca, pode não eliminar
100% em todas as máquinas (mais perceptível em notebooks mais antigos
ou com placas de vídeo integradas mais fracas).
"""


def fix_scroll_ghosting(scrollable_frame):
    """Aplica a mitigação num CTkScrollableFrame já criado."""
    canvas = getattr(scrollable_frame, "_parent_canvas", None)
    if canvas is None:
        return

    def _force_redraw(_event=None):
        scrollable_frame.after(1, scrollable_frame.update_idletasks)

    canvas.bind("<MouseWheel>", _force_redraw, add="+")
