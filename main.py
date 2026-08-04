"""
ACE Helper — ponto de entrada.

O app precisa rodar como administrador porque os módulos de Tweaks e
Debloat mexem no registro do Windows e removem pacotes do sistema.
Se não estiver elevado, ele se reinicia automaticamente pedindo UAC.
"""

import sys
import os
import ctypes


def is_admin() -> bool:
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def relaunch_as_admin():
    params = " ".join([f'"{arg}"' for arg in sys.argv])
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable, f'"{os.path.abspath(sys.argv[0])}" {params}', None, 1
    )


def _avisar_dependencia_faltando(detalhe: str = ""):
    """Mostra um aviso simples (tkinter puro, sem CustomTkinter) caso
    alguma dependência não esteja disponível, em vez de um traceback cru.
    Mostra o erro real (detalhe) pra facilitar o diagnóstico."""
    try:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        mensagem = (
            "O ACE Helper não conseguiu carregar uma dependência.\n\n"
            "Tente instalar rodando no terminal:\n"
            "pip install -r requirements.txt\n\n"
        )
        if detalhe:
            mensagem += f"Detalhe técnico do erro:\n{detalhe}"
        messagebox.showerror("Dependência faltando", mensagem)
        root.destroy()
    except Exception:
        print("Dependência faltando. Detalhe:", detalhe)
        print("Instale com 'pip install -r requirements.txt'")


def main():
    if os.name == "nt" and not is_admin():
        relaunch_as_admin()
        sys.exit()

    try:
        from gui.main_window import MainWindow
    except Exception as e:
        import traceback
        traceback.print_exc()  # também imprime no console, se houver um
        _avisar_dependencia_faltando(f"{type(e).__name__}: {e}")
        sys.exit(1)

    app = MainWindow()
    app.mainloop()


if __name__ == "__main__":
    main()
