#!/usr/bin/env python3
"""
Atualiza a disponibilidade real e regenera o dados.js que a app lê.

    python3 atualizar.py        # o maximo que cada clube permitir

Estado das plataformas, a 10 de setembro de 2026:

  Play Padel Madeira      MatchPoint   grelha pública, funciona
  Quinta do Padel         MatchPoint   exige sessao iniciada; cookie HttpOnly,
                                       recolhido a mao com um browser autenticado
  Centro de Padel e Lazer Aircourts    slots só com sessão, sem acesso
  Padel Centro Caniço     Aircourts    slots só com sessão, sem acesso
  Jardins Panorâmicos     Field        plataforma aparentemente encerrada
  Quinta Magnólia         SIMplifica   exige registo no portal do Governo

Os clubes sem acesso ficam com o horário de funcionamento, e a app diz
claramente que não sabe se estão livres.
"""

import json
import datetime
import pathlib
import sys

AQUI = pathlib.Path(__file__).parent
# Cada clube tem a sua antecedencia maxima de reserva. Recolhe-se o que cada
# um deixa, em vez de cortar todos pelo mais curto.
DIAS_POR_CLUBE = {
    "play-padel-madeira": 30,   # MatchPoint publico, aceita ate 30 dias
    "jardim-panoramico": 15,    # Field publico
}
DIAS_OMISSAO = 15

LEITORES = {}
try:
    import matchpoint
    LEITORES["play-padel-madeira"] = matchpoint.grelha
except ImportError:
    print("aviso: matchpoint.py não encontrado, sem disponibilidade real",
          file=sys.stderr)

try:
    import field
    LEITORES["jardim-panoramico"] = field.grelha
except ImportError:
    print("aviso: field.py não encontrado, sem disponibilidade do Jardim Panorâmico",
          file=sys.stderr)


def main():
    d = json.loads((AQUI / "dados.json").read_text())
    hoje = datetime.date.today()
    total = 0

    for clube in d["clubes"]:
        leitor = LEITORES.get(clube["id"])
        if not leitor:
            # Sem leitor automatico: PRESERVA o que la esta. Alguns clubes
            # (Quinta do Padel) sao recolhidos a mao com sessao iniciada e
            # apagar aqui destruiria esse trabalho a cada execucao.
            continue

        limite = DIAS_POR_CLUBE.get(clube["id"], DIAS_OMISSAO)
        disp = {}
        for i in range(limite):
            data = hoje + datetime.timedelta(days=i)
            try:
                g = leitor(data)
                disp[data.isoformat()] = {
                    "abertura": g["abertura"],
                    "fecho": g["fecho"],
                    "passo": g["passo_min"],
                    "campos": [
                        {"nome": c["nome"], "ocupado": [list(o) for o in c["ocupado"]]}
                        for c in g["campos"]
                    ],
                }
                total += 1
            except Exception as e:
                print(f"  {clube['id']} {data}: {type(e).__name__}: {e}",
                      file=sys.stderr)
        clube["disponibilidade"] = disp
        if disp:
            clube["disponibilidade_em"] = datetime.datetime.now().astimezone().isoformat()
        print(f"  {clube['id']}: {len(disp)} dias com disponibilidade real")

    d["atualizado"] = datetime.datetime.now().astimezone().isoformat()

    (AQUI / "dados.json").write_text(json.dumps(d, ensure_ascii=False, indent=2))
    (AQUI / "dados.js").write_text(
        "// Gerado por atualizar.py. Nao editar a mao.\nwindow.DADOS = "
        + json.dumps(d, ensure_ascii=False, indent=2) + ";\n"
    )
    print(f"\ndados.js atualizado ({total} dias de disponibilidade real).")


if __name__ == "__main__":
    main()
