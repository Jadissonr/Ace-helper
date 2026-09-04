# ACE Helper

App de otimização para Windows 10/11 focado em gamers e profissionais
de esports — tweaks de performance, debloat, plano de energia e
instalação de plataformas, navegadores e ferramentas essenciais, tudo
num só lugar.

## Como usar

Abra o **PowerShell** e rode:

```powershell
irm https://raw.githubusercontent.com/Jadissonr/Ace-helper/main/install.ps1 | iex
```

Isso baixa e abre o ACE Helper automaticamente, além de criar um
atalho na área de trabalho pras próximas vezes. **Não precisa instalar
Python, CustomTkinter ou nada além disso** — o app já vem pronto
dentro do executável.

Na primeira abertura, o app vai pedir uma **chave de acesso** e
permissão de administrador (necessária pros módulos de Tweaks e
Debloat, que mexem no registro do Windows).

## O que o app faz

- **Instalar Apps** — plataformas de jogos (Steam, Epic, Riot, Battle.net...),
  navegadores, Discord, OBS, ferramentas de performance e mais, direto
  via winget
- **Tweaks** — ajustes de performance e privacidade no registro do
  Windows, com botão de aplicar o pacote recomendado de uma vez, plano
  de energia "Ultimate Performance" com um clique, atualização do
  driver NVIDIA, e papel de parede da ACE aplicado automaticamente
  após os tweaks
- **Debloat** — remove aplicativos pré-instalados desnecessários do
  Windows, com opção de restaurar

Antes de qualquer alteração no sistema, o ACE Helper cria
automaticamente um ponto de restauração do Windows.

## Documentação técnica

Documentação de desenvolvimento (como rodar a partir do código-fonte,
estrutura do projeto, como compilar, como configurar a chave de
acesso, como publicar uma nova versão) está em
[docs/DEVELOPMENT.md](docs/DEVELOPMENT.md).

## Feedback

Encontrou um bug ou tem uma sugestão? Use o botão **💬 Feedback**
dentro do próprio app, ou abra uma
[issue aqui no repositório](https://github.com/Jadissonr/Ace-helper/issues/new).
