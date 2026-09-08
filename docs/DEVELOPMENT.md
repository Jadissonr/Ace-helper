# Desenvolvimento — ACE Helper

Documentação técnica pra quem for mexer no código, compilar o `.exe`
ou publicar uma nova versão. Se você só quer usar o app, veja o
[README.md](../README.md).

## Rodando a partir do código-fonte

Requer **Python 3.10+**.

```
pip install -r requirements.txt
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
│   ├── debloat.py           # remove/restaura apps UWP
│   ├── restore_point.py     # cria ponto de restauração do Windows antes de tweaks/debloat
│   ├── power_plan.py        # ativa/reverte o plano de energia Ultimate Performance
│   ├── nvidia_driver.py     # checa e instala atualização do driver NVIDIA (API não-oficial)
│   ├── network_tools.py     # DNS (limpar/trocar), reset TCP/IP, teste de latência
│   ├── startup_manager.py   # lista e ativa/desativa itens de inicialização do Windows
│   ├── feedback.py          # abre GitHub Issue pré-preenchida
│   ├── auth.py              # valida a chave de acesso e o cache local de dispositivo autorizado
│   ├── device.py            # obtém o fingerprint (MachineGuid) do dispositivo
│   ├── wallpaper.py         # define o papel de parede da ACE após aplicar tweaks
│   ├── updater.py           # checa E aplica auto-atualização do próprio ACE Helper (só funciona no .exe)
│   ├── system_stats.py      # CPU/RAM/disco e status de admin (painel Início)
│   ├── paths.py             # resolução de caminhos de assets (compatível com .exe)
│   └── logger.py            # log de ações em ~/ACEHelper/logs/
├── data/
│   ├── games_list.json      # lista de plataformas/jogos/apps instaláveis
│   ├── tweaks_list.json     # lista de tweaks de registro (valor ativado/original)
│   └── debloat_list.json    # lista de apps UWP disponíveis para remoção
├── assets/
│   ├── icon.ico             # ícone do app (usado na janela e no .exe)
│   ├── icon.png             # ícone com fundo, para outros usos
│   ├── logo_transparent.png # logo usada no header da interface
│   ├── wallpaper.png        # papel de parede 1920x1080 aplicado após tweaks
│   └── app_icons/           # ícones-monograma gerados para cada app da aba Instalar
├── gui/
│   ├── theme.py             # paleta de cores e fontes centralizadas (tema gamer/neon)
│   ├── sidebar.py           # barra lateral de navegação (Início/Instalar/Tweaks/Debloat)
│   ├── auth_window.py       # tela de chave de acesso (abre antes do app principal)
│   ├── main_window.py       # janela principal (sidebar + páginas)
│   ├── home_tab.py          # página "Início" — estatísticas do sistema e atalhos
│   ├── installer_tab.py     # página "Instalar Apps" (funcional)
│   ├── tweaks_tab.py        # página "Tweaks" (funcional)
│   ├── network_tab.py       # página "Rede" — DNS, cache, reset TCP/IP, teste de latência
│   ├── startup_tab.py       # página "Inicialização" — ativa/desativa programas de boot
│   ├── debloat_tab.py       # página "Debloat" (funcional)
│   ├── scroll_fix.py        # mitigação do bug de "ghosting" ao rolar listas (bug do CustomTkinter)
│   └── progress_widget.py   # barra de progresso + status reutilizada nas páginas
├── cloudflare-worker/
│   └── worker.js            # código do Worker que valida as chaves de acesso
└── requirements.txt
```

## Adicionando novas plataformas/jogos/apps

Edite `data/games_list.json` e adicione um item com `id` (slug único,
usado pra achar o ícone), `nome`, `categoria` (uma das 3 já existentes:
`Plataformas de Jogos`, `Navegadores` ou `Utilitários` — pra criar uma
seção nova, adicione o nome dela em `CATEGORIA_ORDEM` no topo de
`gui/installer_tab.py`), `winget_id` (descubra com
`winget search <nome>`), `cor` (hex, cor de fundo do ícone-monograma
padrão) e `sigla` (1-3 letras mostradas no ícone). Depois gere o ícone
correspondente em `assets/app_icons/<id>.png` (128x128).

Se você tiver o ícone oficial do app (baixado do brand kit da empresa,
por exemplo) e quiser usar em vez do monograma gerado, é só substituir
o arquivo em `assets/app_icons/<id>.png` pelo ícone real — o app usa
o que estiver lá, sem precisar mexer em código.

## Adicionando novos tweaks

Edite `data/tweaks_list.json` e adicione um item com `id`, `nome`,
`descricao`, uma lista `entries` (um tweak pode mexer em mais de uma
chave de registro ao mesmo tempo) e um campo `standard` (`true`/`false`
— define se ele entra no botão "Aplicar Tweak Padrão"). Cada entry
precisa de `hive` (`HKEY_LOCAL_MACHINE` ou `HKEY_CURRENT_USER`),
`path`, `value_name`, `value_type` (`DWORD`, `QWORD` ou `STRING`),
`value_ativado` e `value_original`. Se `value_original` for `null`,
significa que a chave não existe por padrão no Windows — nesse caso,
"reverter" apaga o valor em vez de escrever outro número.

## Adicionando novos apps ao Debloat

Edite `data/debloat_list.json` e adicione um item com `id`, `nome`,
`descricao`, `appx_name` (o nome do pacote UWP — descubra com
`Get-AppxPackage | Select Name` no PowerShell) e `standard`
(`true`/`false`). A remoção é feita só para o usuário atual (sem
`-AllUsers`), o que é o que permite o botão "Restaurar" funcionar na
maioria dos casos.

## Chave de acesso (Cloudflare Worker)

O código do ACE Helper é público no GitHub, mas abrir o app exige uma
chave de acesso válida — validada contra um Cloudflare Worker que só
você controla. A lista de chaves nunca fica no código nem no `.exe`.

### Publicando o Worker (pelo painel do Cloudflare, sem instalar nada)

1. Crie uma conta gratuita em [dash.cloudflare.com](https://dash.cloudflare.com)
2. No menu lateral, vá em **Workers & Pages** → **Create** → **Create Worker**
3. Dê um nome (ex: `ace-helper-auth`) e clique em **Deploy** (cria um worker padrão de exemplo)
4. Clique em **Edit code**
5. Apague o conteúdo padrão e cole o conteúdo de `cloudflare-worker/worker.js`
   deste repositório
6. Troque as chaves de exemplo no array `VALID_KEYS` pelas suas
   chaves reais (invente strings únicas, ex: `ACE-JADS-2026-XPTO`)
7. Clique em **Save and Deploy**
8. Copie a URL do worker, que aparece no topo da página (algo como
   `https://ace-helper-auth.SEU-USUARIO.workers.dev`)

### Configurando o app pra usar o Worker

1. Abra `core/auth.py`
2. Troque o valor de `WORKER_URL` pela URL que você copiou no passo 8
3. Recompile o `.exe` normalmente

### Adicionando ou revogando chaves depois

Edite o array `VALID_KEYS` no editor do Worker (mesma tela do passo 4)
e clique em **Save and Deploy** de novo — não precisa recompilar nem
tocar no app.

### "Esquecendo" um dispositivo já autorizado

Depois que uma chave é validada com sucesso numa máquina, o ACE Helper
guarda um identificador local (`MachineGuid` do Windows) em
`%USERPROFILE%\ACEHelper\auth_cache.json` e para de pedir a chave
nessa máquina. Se precisar que ela peça de novo (ex: você revogou a
chave dessa pessoa e quer forçar uma nova validação), apague esse
arquivo — na próxima abertura do app, a tela de chave volta a
aparecer.

## Compilando e publicando uma nova versão

1. Compile o app pra `.exe`. O CustomTkinter precisa que os assets
   internos dele sejam incluídos manualmente no build, senão o `.exe`
   abre sem estilo nenhum — e as pastas `assets/` (ícone e logo) e
   `data/` (listas de tweaks/apps/jogos) também precisam ser embutidas
   manualmente, senão o app abre e trava na hora de carregar as listas:
   ```
   pip install pyinstaller
   python -m PyInstaller --onefile --windowed --name ACEHelper --icon assets/icon.ico --add-data "assets;assets" --add-data "data;data" --collect-all customtkinter --collect-all certifi --collect-all psutil main.py
   ```
   (no Windows o separador do `--add-data` é `;`; em Linux/Mac seria `:`)
   O executável final fica em `dist/ACEHelper.exe`.

2. Suba o código pro GitHub (sem a pasta `dist/` e `build/`, essas são
   geradas localmente — já estão no `.gitignore`).

3. No GitHub, crie um **Release** (aba "Releases" → "Create a new release")
   e anexe o `ACEHelper.exe` gerado no passo 1. **Importante**: a tag
   do Release (ex: `v0.4.0`) deve bater com `APP_VERSION` em
   `gui/main_window.py` — é essa comparação que faz o aviso de
   atualização dentro do app funcionar corretamente.

4. Pronto — o `install.ps1` já aponta pro repositório certo e sempre
   busca automaticamente o `.exe` mais recente anexado no último
   Release (usa a API do GitHub pra achar o "latest release"), então
   não precisa editar nada nele depois da primeira configuração.

## Atualização de driver NVIDIA

O botão "Driver NVIDIA" na aba Tweaks depende de um endpoint **não
documentado oficialmente pela NVIDIA**, mas usado publicamente há anos
por ferramentas open-source de atualização de driver (referência:
[ZenitH-AT/nvidia-update](https://github.com/ZenitH-AT/nvidia-update)).
Pontos importantes:

- Detecta a GPU e a versão atual via `nvidia-smi` (só funciona se já
  existir algum driver NVIDIA instalado — se a pessoa nunca instalou
  nenhum driver, o `nvidia-smi` não existe ainda, e o botão vai avisar
  que não encontrou GPU).
- Precisa de acesso à internet aos domínios `nvidia.com` e
  `gfwsl.geforce.com`.
- Como é uma API não-oficial, pode parar de funcionar sem aviso se a
  NVIDIA mudar o formato — nesse caso, o app não trava, só mostra erro
  ao checar/atualizar.
- O driver é instalado com as flags `-s -noreboot` (silencioso, sem
  reiniciar automaticamente). Um ponto de restauração é criado antes,
  igual os outros tweaks.

## Auto-atualização do ACE Helper

Quando o app detecta uma versão nova nos Releases do GitHub, ele
oferece **"Atualizar agora"** (só quando rodando como `.exe` — rodando
do código-fonte, só oferece abrir a página do Release manualmente).

Como o Windows não deixa substituir um `.exe` enquanto ele está
rodando, o fluxo é:

1. Baixa o novo `.exe` pra `ACEHelper_new.exe`, na mesma pasta do atual
2. Gera um `.bat` temporário que fica esperando o processo atual
   (identificado pelo PID) encerrar
3. O app se fecha (`self.destroy()`)
4. O `.bat` detecta que o processo sumiu, substitui o `.exe` antigo
   pelo novo, reabre o app, e se autodeleta

Isso significa que a tag do próximo Release **precisa** ter um
`.exe` anexado com esse mesmo padrão de nome (`ACEHelper.exe`) pra
esse fluxo funcionar — segue o mesmo processo de publicação de sempre.

## Créditos

Parte da lista de tweaks (a partir do "Histórico de Atividades" em
diante) e a lista de apps do Debloat são baseadas no excelente
[WinUtil do Chris Titus Tech](https://github.com/ChrisTitusTech/winutil),
adaptadas para o formato e o motor do ACE Helper.

O ícone/logo em `assets/` é a marca real do ACE (ACE Bootcamp),
recortada e adaptada (fundo transparente, versão quadrada com fundo
preto arredondado pro `.ico`) para uso no ACE Helper.
