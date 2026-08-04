# ACE Helper

App de otimização para Windows 10/11 — tweaks, debloat e instalação de
plataformas/jogos direto pelo winget.

## Como rodar

Requer **Python 3.10+** instalado no Windows.

Instale as dependências (só o CustomTkinter, usado pra interface):
```
pip install -r requirements.txt
```

Depois:
```
python main.py
```

O app pede elevação de administrador automaticamente (UAC) na abertura,
pois os módulos de Tweaks e Debloat precisam mexer no registro e remover
pacotes do sistema.

## Estrutura

```
ace-helper/
├── main.py                 # ponto de entrada + checagem de admin
├── core/
│   ├── installer.py         # wrapper em cima do winget
│   ├── tweaks.py            # aplica/reverte tweaks de registro
│   ├── restore_point.py     # cria ponto de restauração do Windows antes de tweaks
│   └── logger.py            # log de ações em ~/ACEHelper/logs/
├── data/
│   ├── games_list.json      # lista de plataformas/jogos instaláveis
│   ├── tweaks_list.json     # lista de tweaks de registro (valor ativado/original)
│   └── debloat_list.json    # lista de apps UWP disponíveis para remoção
├── assets/
│   ├── icon.ico             # ícone do app (usado na janela e no .exe)
│   ├── icon.png             # ícone com fundo, para outros usos
│   └── logo_transparent.png # logo usada no header da interface
├── gui/
│   ├── main_window.py       # janela principal com abas
│   ├── installer_tab.py     # aba "Instalar Jogos" (funcional)
│   ├── tweaks_tab.py        # aba "Tweaks" (funcional)
│   └── debloat_tab.py       # aba "Debloat" (funcional)
└── requirements.txt
```

## Status atual

- [x] Janela principal com 3 abas
- [x] Aba "Instalar Jogos" funcional (via winget, roda em thread separada)
- [x] Aba "Tweaks" funcional (aplica/reverte ajustes de registro, mostra status atual, roda em thread separada)
- [x] Botão "Aplicar Tweak Padrão" — aplica de uma vez o conjunto de 13 ajustes recomendados, sem precisar selecionar item por item
- [x] Ponto de restauração do Windows criado automaticamente antes de qualquer tweak ou debloat ser aplicado/revertido
- [x] Checagem de admin + auto-elevação (UAC)
- [x] Log de ações em arquivo
- [x] Aba "Debloat" funcional (remove/restaura apps UWP, mostra status Instalado/Removido, botão "Debloat Padrão" com 12 apps recomendados)
- [x] Interface modernizada com CustomTkinter (dark mode, cores de destaque, badges "Padrão")
- [x] Identidade visual: tema preto + roxo claro, logo/ícone próprio (monograma "A")

## Adicionando novas plataformas/jogos

Basta editar `data/games_list.json` e adicionar um item com `nome`,
`categoria` e `winget_id` (descubra o ID com `winget search <nome>`).

## Adicionando novos tweaks

Edite `data/tweaks_list.json` e adicione um item com `id`, `nome`,
`descricao`, uma lista `entries` (um tweak pode mexer em mais de uma
chave de registro ao mesmo tempo) e um campo `standard` (`true`/`false`
— define se ele entra no botão "Aplicar Tweak Padrão"). Cada entry precisa de `hive`
(`HKEY_LOCAL_MACHINE` ou `HKEY_CURRENT_USER`), `path`, `value_name`,
`value_type` (`DWORD`, `QWORD` ou `STRING`), `value_ativado` e
`value_original`. Se `value_original` for `null`, significa que a
chave não existe por padrão no Windows — nesse caso, "reverter" apaga
o valor em vez de escrever outro número.

## Adicionando novos apps ao Debloat

Edite `data/debloat_list.json` e adicione um item com `id`, `nome`,
`descricao`, `appx_name` (o nome do pacote UWP — descubra com
`Get-AppxPackage | Select Name` no PowerShell) e `standard`
(`true`/`false`). A remoção é feita só para o usuário atual (sem
`-AllUsers`), o que é o que permite o botão "Restaurar" funcionar na
maioria dos casos.

## Créditos

Parte da lista de tweaks (a partir do "Histórico de Atividades" em
diante) e a lista de apps do Debloat são baseadas no excelente
[WinUtil do Chris Titus Tech](https://github.com/ChrisTitusTech/winutil),
adaptadas para o formato e o motor do ACE Helper.

O ícone/logo em `assets/` é a marca real do ACE (ACE Bootcamp),
recortada e adaptada (fundo transparente, versão quadrada com fundo
preto arredondado pro `.ico`) para uso no ACE Helper.

## Distribuindo via PowerShell (rodar em qualquer PC sem Python instalado)

1. Compile o app pra `.exe`. O CustomTkinter precisa que os assets
   internos dele sejam incluídos manualmente no build, senão o `.exe`
   abre sem estilo nenhum — e a pasta `assets/` (ícone e logo) também
   precisa ser embutida manualmente:
   ```
   pip install pyinstaller
   pyinstaller --onefile --windowed --name ACEHelper --icon assets/icon.ico --add-data "assets;assets" --collect-all customtkinter main.py
   ```
   (no Windows o separador do `--add-data` é `;`; em Linux/Mac seria `:`)
   O executável final fica em `dist/ACEHelper.exe`.

2. Crie o repositório no GitHub e suba o código (sem a pasta `dist/`
   e `build/`, essas são geradas localmente — adicione ao `.gitignore`).

3. No GitHub, crie um **Release** (aba "Releases" → "Create a new release")
   e anexe o `ACEHelper.exe` gerado no passo 1.

4. Edite `install.ps1` e troque `SEU_USUARIO/ace-helper` pelo caminho real
   do seu repositório (ex: `jadisson/ace-helper`).

5. Faça commit do `install.ps1` atualizado.

6. Qualquer pessoa (inclusive você, de qualquer PC) roda:
   ```
   irm https://raw.githubusercontent.com/SEU_USUARIO/ace-helper/main/install.ps1 | iex
   ```
   Isso baixa o `.exe` mais recente do Release e executa — sem precisar
   de Python instalado na máquina de destino.
