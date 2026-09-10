#!/usr/bin/env python3
"""
Lê a disponibilidade pública do Play Padel Madeira (plataforma MatchPoint).

O site publica a grelha de reservas sem login. Este módulo pede a mesma
informação que a página pede a si própria e devolve, por campo, os blocos
ocupados e os blocos livres.

    python3 matchpoint.py            # mostra a grelha de hoje
    python3 matchpoint.py 2026-09-15 # de uma data especifica
"""

import json
import re
import sys
import datetime
import http.cookiejar
import urllib.request

BASE = "https://playpadelmadeira-pt.matchpoint.com.es"
GRELHA = BASE + "/Booking/Grid.aspx"
SERVICO = BASE + "/booking/srvc.aspx/ObtenerCuadro"
ID_CUADRO = 4  # Padel

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36")


def _abridor():
    jar = http.cookiejar.CookieJar()
    return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))


def _chave(abridor):
    """A página guarda uma chave de sessão numa variável global de nome
    aleatório. Procura-a no HTML."""
    req = urllib.request.Request(GRELHA, headers={"User-Agent": UA})
    html = abridor.open(req, timeout=25).read().decode("utf-8", "replace")
    padroes = [
        r"var\s+[A-Za-z0-9_]{8,20}\s*=\s*['\"]([A-Za-z0-9+/]{30,}={0,2})['\"]",
        r"[A-Za-z0-9_]{8,20}\s*=\s*['\"]([A-Za-z0-9+/]{40,}={0,2})['\"]\s*;",
    ]
    for p in padroes:
        for m in re.finditer(p, html):
            valor = m.group(1)
            if "VIEWSTATE" not in valor and len(valor) < 200:
                return valor
    raise RuntimeError("chave de sessão não encontrada no HTML da grelha")


def grelha(data=None):
    """Devolve {'abertura','fecho','campos':[{'nome','ocupado':[(ini,fim)]}]}."""
    data = data or datetime.date.today()
    if isinstance(data, str):
        data = datetime.date.fromisoformat(data)

    abridor = _abridor()
    chave = _chave(abridor)

    corpo = json.dumps({
        "idCuadro": ID_CUADRO,
        "fecha": data.strftime("%d/%m/%Y"),
        "key": chave,
    }).encode()

    req = urllib.request.Request(SERVICO, data=corpo, headers={
        "User-Agent": UA,
        "Content-Type": "application/json; charset=utf-8",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": GRELHA,
    })
    resposta = json.loads(abridor.open(req, timeout=25).read().decode("utf-8"))
    d = resposta.get("d") or {}
    if not d.get("Columnas"):
        raise RuntimeError("resposta sem colunas (chave inválida ou grelha fechada)")

    campos = []
    for col in d["Columnas"]:
        ocupado = sorted(
            (o["StrHoraInicio"], o["StrHoraFin"]) for o in col.get("Ocupaciones", [])
        )
        campos.append({"nome": col.get("TextoPrincipal", "?"), "ocupado": ocupado})

    return {
        "data": data.isoformat(),
        "abertura": d.get("StrHoraInicio"),
        "fecho": d.get("StrHoraFin"),
        "passo_min": int(60 / int(d.get("PartesPorHora") or 2)),
        "campos": campos,
    }


def _min(h):
    a, b = h.split(":")
    return int(a) * 60 + int(b)


def livres(g, duracao=90):
    """Horas de início livres em TODOS os campos, dada uma duração em minutos."""
    ini, fim = _min(g["abertura"]), _min(g["fecho"])
    passo = g["passo_min"]
    resultado = {}
    for campo in g["campos"]:
        blocos = [(_min(a), _min(b)) for a, b in campo["ocupado"]]
        horas = []
        t = ini
        while t + duracao <= fim:
            if not any(t < f and t + duracao > i for i, f in blocos):
                horas.append(f"{t // 60:02d}:{t % 60:02d}")
            t += passo
        resultado[campo["nome"]] = horas
    return resultado


if __name__ == "__main__":
    alvo = sys.argv[1] if len(sys.argv) > 1 else None
    g = grelha(alvo)
    print(f"Play Padel Madeira — {g['data']}  ({g['abertura']} às {g['fecho']})\n")
    livre = livres(g)
    for campo in g["campos"]:
        print(f"  {campo['nome']}")
        print(f"    ocupado: {', '.join(a + '-' + b for a, b in campo['ocupado']) or 'nada'}")
        h = livre[campo["nome"]]
        print(f"    livre 1h30: {', '.join(h) if h else 'nada'}\n")
