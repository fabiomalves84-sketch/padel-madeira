#!/usr/bin/env python3
"""
Atualiza a disponibilidade real dos campos e regenera dados.js.

    python3 atualizar.py              # atualiza os proximos 7 dias
    python3 atualizar.py --descobrir  # despeja a resposta crua de cada plataforma

AVISO HONESTO: os adaptadores abaixo foram escritos contra o formato conhecido
das APIs internas do Playtomic e do Aircourts, mas NAO foram testados contra os
servidores reais. Corre com --descobrir primeiro, ve o que volta em bruto,
e ajusta o parser. Estas APIs nao sao publicas e podem mudar sem aviso.
"""

import json, sys, datetime, pathlib, urllib.request, urllib.parse, urllib.error

AQUI = pathlib.Path(__file__).parent
DIAS = 7
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/128 Safari/537.36"


def http(url, dados=None, cabecalhos=None, metodo=None):
    h = {"User-Agent": UA, "Accept": "application/json, text/plain, */*"}
    h.update(cabecalhos or {})
    corpo = None
    if dados is not None:
        corpo = urllib.parse.urlencode(dados).encode()
        h.setdefault("Content-Type", "application/x-www-form-urlencoded")
    req = urllib.request.Request(url, data=corpo, headers=h, method=metodo)
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.read().decode("utf-8", "replace")


# --------------------------------------------------------------- adaptadores

def playtomic(clube, data):
    """Devolve lista de horas livres 'HH:MM' ou None se falhar."""
    tid = clube.get("playtomic_tenant_id")
    if not tid:
        return None
    q = urllib.parse.urlencode({
        "sport_id": "PADEL",
        "tenant_id": tid,
        "local_start_min": f"{data}T00:00:00",
        "local_start_max": f"{data}T23:59:59",
    })
    bruto = http(f"https://api.playtomic.io/v1/availability?{q}")
    horas = set()
    for campo in json.loads(bruto):
        for s in campo.get("slots", []):
            horas.add(s["start_time"][:5])
    return sorted(horas)


def aircourts(clube, data):
    slug = clube.get("aircourts_slug")
    if not slug:
        return None
    bruto = http(
        "https://www.aircourts.com/index.php/api/search_with_club",
        dados={"date": data, "sport": "1", "club_id": slug, "start_time": "00:00"},
    )
    j = json.loads(bruto)
    horas = set()
    for res in j.get("results", []):
        for s in res.get("slots", []):
            horas.add(str(s.get("start", ""))[:5])
    horas.discard("")
    return sorted(horas)


ADAPTADORES = {"playtomic": playtomic, "aircourts": aircourts}


# --------------------------------------------------------------------- fluxo

def descobrir(d):
    saida = AQUI / "bruto"
    saida.mkdir(exist_ok=True)
    hoje = datetime.date.today().isoformat()
    for c in d["clubes"]:
        for nome in ADAPTADORES:
            chave = f"{nome}_tenant_id" if nome == "playtomic" else f"{nome}_slug"
            if not c.get(chave):
                continue
            try:
                r = ADAPTADORES[nome](c, hoje)
                print(f"  OK   {c['id']:24} {nome:10} -> {r}")
            except Exception as e:
                print(f"  FALHA {c['id']:24} {nome:10} -> {type(e).__name__}: {e}")
        if c.get("url_reserva"):
            try:
                html = http(c["url_reserva"])
                f = saida / f"{c['id']}.html"
                f.write_text(html)
                print(f"       pagina guardada em bruto/{f.name} ({len(html)} bytes)")
            except Exception as e:
                print(f"       pagina falhou: {type(e).__name__}: {e}")


def atualizar(d):
    hoje = datetime.date.today()
    for c in d["clubes"]:
        adaptador = None
        if c.get("playtomic_tenant_id"):
            adaptador = playtomic
        elif c.get("aircourts_slug"):
            adaptador = aircourts
        if not adaptador:
            continue
        disp = {}
        for i in range(DIAS):
            data = (hoje + datetime.timedelta(days=i)).isoformat()
            try:
                horas = adaptador(c, data)
                if horas is not None:
                    disp[data] = horas
            except Exception as e:
                print(f"  {c['id']} {data}: {type(e).__name__}: {e}", file=sys.stderr)
        if disp:
            c["disponibilidade"] = disp
            print(f"  {c['id']}: {sum(len(v) for v in disp.values())} slots em {len(disp)} dias")
        else:
            print(f"  {c['id']}: sem dados, mantem horario base")
    d["atualizado"] = datetime.datetime.now().astimezone().isoformat()


def main():
    d = json.loads((AQUI / "dados.json").read_text())
    if "--descobrir" in sys.argv:
        print("Modo descoberta. Nada e gravado em dados.js.\n")
        descobrir(d)
        return
    print("A atualizar disponibilidade...\n")
    atualizar(d)
    (AQUI / "dados.json").write_text(json.dumps(d, ensure_ascii=False, indent=2))
    (AQUI / "dados.js").write_text(
        "// Gerado por atualizar.py. Nao editar a mao.\nwindow.DADOS = "
        + json.dumps(d, ensure_ascii=False, indent=2) + ";\n"
    )
    print("\ndados.js atualizado.")


if __name__ == "__main__":
    main()
