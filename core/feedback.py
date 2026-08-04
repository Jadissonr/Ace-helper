"""
Abre o navegador numa página de "Nova Issue" já pré-preenchida no
repositório do ACE Helper no GitHub. Não precisa de credenciais, não
manda nada automaticamente — o usuário revisa e clica em "Submit new
issue" ele mesmo, do jeito que o GitHub já funciona.
"""

import webbrowser
from urllib.parse import quote

REPO = "Jadissonr/Ace-helper"

TITLE_TEMPLATE = "Feedback: "
BODY_TEMPLATE = (
    "**Tipo:** (bug / sugestão / elogio — apague o que não for)\n\n"
    "**Descreva aqui:**\n\n\n"
    "**Passos para reproduzir (se for um bug):**\n\n\n"
    "**Versão do ACE Helper:** \n"
)


def open_feedback_page():
    """Abre o navegador padrão numa issue nova já com título e corpo
    sugeridos. Retorna (sucesso, mensagem)."""
    url = (
        f"https://github.com/{REPO}/issues/new"
        f"?title={quote(TITLE_TEMPLATE)}"
        f"&body={quote(BODY_TEMPLATE)}"
        f"&labels=feedback"
    )
    try:
        webbrowser.open(url)
        return True, "Página de feedback aberta no navegador."
    except Exception as e:
        return False, f"Não foi possível abrir o navegador: {e}"
