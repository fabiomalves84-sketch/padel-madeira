# Padel Madeira

Os campos de padel da ilha num sítio só: grelha de horários, preços, formas de
pagamento e link direto para a plataforma de reserva de cada clube.

Sem build, sem dependências. HTML, CSS e JS num ficheiro.

## Correr

```bash
cd ~/Sites/padel-madeira
python3 -m http.server 8000
```

Abre `http://localhost:8000`. No iPhone, na mesma rede Wi-Fi, usa o IP do Mac
(`ipconfig getifaddr en0`), depois Partilhar → Adicionar ao ecrã principal.

## Atualizar a disponibilidade

```bash
python3 atualizar.py
```

Atualiza o **Play Padel Madeira**, que é público. Corre isto antes de usares a
app, ou agenda com launchd.

A **Quinta do Padel** não pode ser atualizada por aqui: exige sessão iniciada e
o cookie de autenticação é HttpOnly, ou seja, não é acessível a partir da
página. Os dados que lá estão foram recolhidos com uma sessão aberta num
browser e ficam estáticos até serem recolhidos outra vez da mesma forma.

## Clubes

| Clube | Concelho | Campos | Plataforma | Tempo real |
|---|---|---|---|---|
| Quinta do Padel | Funchal | 5 cobertos | MatchPoint | Sim, com sessão |
| Play Padel Madeira | Funchal | 3 | MatchPoint | Sim, público |
| Centro de Padel e Lazer | Funchal | 3 cobertos | Aircourts | Não |
| Jardins Panorâmicos do Lido | Funchal | 3 | Field (extinta) | Não |
| Quinta Magnólia | Funchal | 3 | SIMplifica | Não |
| Padel Centro Caniço | Santa Cruz | 2 | Aircourts | Não |
| Nexo Padel Club | Câmara de Lobos | 2 | Playtomic | Não |
| Lobos Park | Câmara de Lobos | ? | SIMplifica | Não |
| Centro Desportivo da Madeira | Ribeira Brava | 2 | Aircourts | Não |
| Padel Porto de Recreio da Calheta | Calheta | 2 | Aircourts | Não |
| Padel Vila Baleira | Porto Santo | 4 | Aircourts | Não |
| Complexo de Ténis e Padel do Porto Santo | Porto Santo | 2 | Aircourts | Não |

**12 espaços, 31 campos.** Preços por hora e campo inteiro, dos que publicam:
Porto Santo Ténis 5€, Ribeira Brava 6€, Calheta 6€, Caniço 8€, Centro de Padel
e Lazer 12€, Vila Baleira 12€.

## Disponibilidade real: o que dá e o que não dá

| Clube | Plataforma | Disponibilidade |
|---|---|---|
| Play Padel Madeira | MatchPoint | **Sim**, grelha pública |
| Quinta do Padel | MatchPoint | **Sim, com sessão iniciada** |
| Nexo Padel Club | Playtomic | Não, o site não mostra grelha |
| Lobos Park | SIMplifica | Não, exige registo |
| Centro de Padel e Lazer | Aircourts | Não, slots só com sessão |
| Padel Centro Caniço | Aircourts | Não, slots só com sessão |
| Jardins Panorâmicos | Field | Plataforma aparentemente encerrada |
| Quinta Magnólia | SIMplifica | Não, exige registo no portal |

Dois clubes em seis dão disponibilidade: o Play Padel Madeira sem login, a Quinta do Padel com sessão iniciada. São 8 campos dos 19 da ilha. Isto foi verificado, não
suposto: o endpoint do Aircourts devolve `slots: []` para todos os clubes do
país, incluindo os maiores de Lisboa e do Porto, e a Quinta do Padel devolve
a página de login.

A app é honesta sobre isto. Onde há dados reais, mostra a grelha com os campos
e as horas livres. Onde não há, mostra o horário de funcionamento e diz que é
preciso confirmar na plataforma do clube.

## Ficheiros

| Ficheiro | O que é |
|---|---|
| `index.html` | A app inteira |
| `dados.json` | Fonte de verdade dos clubes. Edita aqui |
| `dados.js` | Gerado. É o que a app lê |
| `atualizar.py` | Atualiza a disponibilidade e regenera o `dados.js` |
| `matchpoint.py` | Lê a grelha pública do Play Padel Madeira |
| `manifest.json`, `icone.png` | Instalação como app no iPhone |

O campo `horario` no `dados.json` é um array de 7 posições que **começa no
domingo**. `["08:00","22:30"]` para abrir, `null` para fechado.

## Qualidade dos dados

Vêm da API do Aircourts, fonte primária:

- **Centro de Padel e Lazer** — R. das Hortas 101, Funchal. 291 647 790.
  3 campos cobertos. Seg-sex 08:00-00:00, sáb 09:00-00:00, dom 10:00-21:00.
  12€/hora. Pagamento no campo à chegada: dinheiro, cheque ou multibanco.
  Cancelamento com 48h.
- **Padel Centro Caniço** — Impasse Est. do Livramento 7, Caniço. 291 602 431.
  2 campos descobertos. Todos os dias 09:00-22:00. 8€/hora. Pré-pagamento
  obrigatório por cartão ou multibanco. Cancelamento até 6h antes.

Os outros quatro têm campos por confirmar. Telefones para fechar as lacunas:

- Quinta do Padel: 931 103 927
- Jardins Panorâmicos: 961 687 191
- Quinta Magnólia: 291 145 788

## Automatizar

`~/Library/LaunchAgents/pt.padelmadeira.atualizar.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>pt.padelmadeira.atualizar</string>
  <key>ProgramArguments</key>
  <array>
    <string>/usr/bin/python3</string>
    <string>/Users/fabioalves/Sites/padel-madeira/atualizar.py</string>
  </array>
  <key>StartInterval</key><integer>3600</integer>
  <key>StandardErrorPath</key><string>/tmp/padel-atualizar.log</string>
</dict></plist>
```

`launchctl load ~/Library/LaunchAgents/pt.padelmadeira.atualizar.plist`

## Limites

Não reserva nem cobra. Reservar dentro da app exigiria acordo comercial com
cada clube e registo como comerciante. É um problema de contratos, não de
código.

O `matchpoint.py` lê um endpoint interno de um site comercial. É informação
que qualquer pessoa vê sem login, e isto é uma ferramenta de uso pessoal. Se
alguma vez for publicado ou usado por muita gente, a conversa muda.
