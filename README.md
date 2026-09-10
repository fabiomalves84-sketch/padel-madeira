# Padel Madeira

Web app que junta os campos de padel da ilha da Madeira num só sítio: horários
clicáveis, preços, formas de pagamento e link direto para a plataforma de
reserva de cada clube.

Sem build, sem dependências. HTML, CSS e JS num ficheiro.

## Clubes cobertos

| Clube | Concelho | Campos | Plataforma |
|---|---|---|---|
| Quinta do Padel | Funchal | 5 (3 cobertos) | App própria |
| Play Padel Madeira | Funchal | 3 | MatchPoint |
| Centro de Padel e Lazer | Funchal | 3 cobertos | Playtomic / Aircourts |
| Jardins Panorâmicos do Lido | Funchal | 3 | Field |
| Padel Centro Caniço | Santa Cruz | 3 | TieSports / Aircourts |
| Quinta Magnólia | Funchal | 3 | SIMplifica |

## Correr localmente

```bash
python3 -m http.server 8000
```

Abre `http://localhost:8000`. No iPhone, na mesma rede Wi-Fi, usa o IP do Mac
(`ipconfig getifaddr en0`), depois Partilhar → Adicionar ao ecrã principal.

Duplo clique no `index.html` também funciona, mas sem instalação como app.

## Ficheiros

| Ficheiro | O que é |
|---|---|
| `index.html` | A app inteira |
| `dados.json` | Fonte de verdade dos clubes. Edita aqui |
| `dados.js` | Gerado a partir do JSON. É o que a app lê |
| `atualizar.py` | Busca disponibilidade real e regenera `dados.js` |
| `manifest.json`, `icone.png` | Instalação como app no iPhone |

## Editar clubes

```bash
# depois de mexer no dados.json
python3 -c "import json;d=json.load(open('dados.json'));open('dados.js','w').write('window.DADOS = '+json.dumps(d,ensure_ascii=False,indent=2)+';')"
```

O campo `horario` é um array de 7 posições que **começa no domingo**.
`["08:00","22:30"]` para abrir, `null` para fechado.

## Disponibilidade real

Os horários mostrados são os de **funcionamento**, não os slots livres.

```bash
python3 atualizar.py --descobrir   # ver o que as APIs devolvem em bruto
python3 atualizar.py               # atualizar dados.js
```

Os adaptadores de Playtomic e Aircourts estão escritos mas **não testados**
contra os servidores reais. MatchPoint, Field, TieSports e SIMplifica não têm
adaptador.

Estas APIs não são públicas. Para uso pessoal o risco é baixo; para um produto
aberto ao público, não é.

## Estado dos dados

A maioria dos clubes da Madeira não publica preços na web aberta. Estão dentro
das apps de reserva, atrás de login. O que está no `dados.json` marcado como
`"confirmado": false` veio de fontes secundárias e pode estar errado.

Para confirmar, é preciso telefonar:

- Quinta do Padel: 931 103 927
- Padel Centro Caniço: 291 934 621
- Jardins Panorâmicos: 961 687 191
- Quinta Magnólia: 291 145 788

## O que isto não faz

Não reserva nem cobra. Reservar dentro da app exigiria acordo comercial com
cada clube e registo como comerciante para processar pagamentos. É um problema
de contratos, não de código.
