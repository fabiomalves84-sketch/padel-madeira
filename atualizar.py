#!/usr/bin/env python3
"""
Atualiza a disponibilidade real e regenera o dados.js que a app lê.

    python3 atualizar.py        # próximos 7 dias

Estado das plataformas, a 10 de setembro de 2026:

  Play Padel Madeira      MatchPoint   grelha pública, funciona
  Quinta do Padel         MatchPoint   exige login, sem acesso
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
DIAS = 7

LEITORES = {}
try:
    import matchpoint
    LEITORES["play-padel-madeira"] = matchpoint.grelha
except ImportError:
    print("aviso: matchpoint.py não encontrado, sem disponibilidade real",
          file=sys.stderr)


def main():
    d = json.loads((AQUI / "dados.json").read_text())
    hoje = datetime.date.today()
    total = 0

    for clube in d["clubes"]:
        leitor = LEITORES.get(clube["id"])
        if not leitor:
            clube["disponibilidade"] = {}
            continue

        disp = {}
        for i in range(DIAS):
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
