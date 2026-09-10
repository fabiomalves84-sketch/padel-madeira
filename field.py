"""Leitor público da disponibilidade do Jardim Panorâmico no Field."""

import datetime
import json
import urllib.request


PROJECT = "field-v2-prod"
CLUB_ID = "f2JIwIOBXaSa95zlDdXI"
BASE = (
    "https://firestore.googleapis.com/v1/projects/"
    f"{PROJECT}/databases/(default)/documents"
)


def _valor(v):
    """Converte um valor tipado do Firestore para um valor normal de Python."""
    if "stringValue" in v:
        return v["stringValue"]
    if "integerValue" in v:
        return int(v["integerValue"])
    if "doubleValue" in v:
        return float(v["doubleValue"])
    if "booleanValue" in v:
        return bool(v["booleanValue"])
    if "timestampValue" in v:
        return v["timestampValue"]
    if "nullValue" in v:
        return None
    if "arrayValue" in v:
        return [_valor(x) for x in v["arrayValue"].get("values", [])]
    if "mapValue" in v:
        return {
            k: _valor(x)
            for k, x in v["mapValue"].get("fields", {}).items()
        }
    return None


def _documento(item):
    doc = item.get("document", item)
    dados = {k: _valor(v) for k, v in doc.get("fields", {}).items()}
    dados.setdefault("id", doc.get("name", "").rsplit("/", 1)[-1])
    return dados


def _consulta(collection, campos, filtros):
    fs = [
        {
            "fieldFilter": {
                "field": {"fieldPath": nome},
                "op": op,
                "value": {"stringValue": valor},
            }
        }
        for nome, op, valor in filtros
    ]
    where = fs[0] if len(fs) == 1 else {"compositeFilter": {"op": "AND", "filters": fs}}
    corpo = {
        "structuredQuery": {
            "select": {"fields": [{"fieldPath": c} for c in campos]},
            "from": [{"collectionId": collection}],
            "where": where,
        }
    }
    pedido = urllib.request.Request(
        BASE + ":runQuery",
        data=json.dumps(corpo).encode(),
        headers={"Content-Type": "application/json", "User-Agent": "PadelMadeira/1.0"},
        method="POST",
    )
    with urllib.request.urlopen(pedido, timeout=25) as resposta:
        return [_documento(x) for x in json.load(resposta) if x.get("document")]


def _minutos(hora):
    h, m = hora.split(":")[:2]
    return int(h) * 60 + int(m)


def _hora(minutos):
    return f"{minutos // 60:02d}:{minutos % 60:02d}"


def grelha(data):
    campos = _consulta(
        "field",
        ["id", "name", "workingHours", "blockedSlots", "disabled", "sports"],
        [("clubId", "EQUAL", CLUB_ID)],
    )
    campos = [
        c for c in campos
        if not c.get("disabled") and "padel" in (c.get("sports") or [])
    ]
    if not campos:
        raise RuntimeError("O Field não devolveu campos de padel")

    # No Field, segunda-feira é 1 e domingo é 7.
    dia_semana = data.isoweekday()
    horas = {}
    for campo in campos:
        horario = next(
            (h for h in campo.get("workingHours", []) if h.get("day") == dia_semana),
            None,
        )
        if horario:
            horas[campo["id"]] = (_minutos(horario["start"]), _minutos(horario["end"]))
    if not horas:
        raise RuntimeError("Clube fechado neste dia")

    abertura = min(x[0] for x in horas.values())
    fecho = max(x[1] for x in horas.values())
    inicio = data.isoformat() + "T00:00:00.000Z"
    fim = data.isoformat() + "T23:59:59.999Z"
    reservas = _consulta(
        "booking",
        ["fieldId", "isoStart", "isoEnd", "status", "type"],
        [
            ("clubId", "EQUAL", CLUB_ID),
            ("isoStart", "GREATER_THAN_OR_EQUAL", inicio),
            ("isoStart", "LESS_THAN_OR_EQUAL", fim),
        ],
    )

    ocupados = {c["id"]: [] for c in campos}
    for reserva in reservas:
        if reserva.get("fieldId") not in ocupados:
            continue
        if reserva.get("status") in ("cancelled", "failed"):
            continue
        if reserva.get("type") == "openMatch" and reserva.get("status") != "booked":
            continue
        if not reserva.get("isoStart") or not reserva.get("isoEnd"):
            continue
        a = reserva["isoStart"].split("T", 1)[1][:5]
        b = reserva["isoEnd"].split("T", 1)[1][:5]
        ocupados[reserva["fieldId"]].append((a, b))

    for campo in campos:
        campo_id = campo["id"]
        if campo_id not in horas:
            ocupados[campo_id].append((_hora(abertura), _hora(fecho)))
            continue
        abre, fecha = horas[campo_id]
        if abre > abertura:
            ocupados[campo_id].append((_hora(abertura), _hora(abre)))
        if fecha < fecho:
            ocupados[campo_id].append((_hora(fecha), _hora(fecho)))
        for bloqueio in campo.get("blockedSlots", []) or []:
            if bloqueio.get("date") == data.isoformat():
                ocupados[campo_id].append((bloqueio["startTime"], bloqueio["endTime"]))

    return {
        "abertura": _hora(abertura),
        "fecho": _hora(fecho),
        "passo_min": 30,
        "campos": [
            {"nome": c.get("name", "Campo"), "ocupado": ocupados[c["id"]]}
            for c in campos
        ],
    }


if __name__ == "__main__":
    print(json.dumps(grelha(datetime.date.today()), ensure_ascii=False, indent=2))
