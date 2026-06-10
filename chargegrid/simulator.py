from chargegrid.models import Allocation, Charger
from chargegrid.predictor import DemandPredictor


SUPPORTED_PROTOCOLS = {
    "OCPP 1.5": "OCPP 1.6-J",
    "OCPP 1.6": "OCPP 1.6-J",
    "OCPP 1.6-J": "OCPP 1.6-J",
    "OCPP 2.0.1": "OCPP 2.0.1",
    "Proprietario": "Adaptador REST -> OCPP 1.6-J",
}


def normalize_protocol(protocol: str) -> str:
    return SUPPORTED_PROTOCOLS.get(protocol, "Protocolo nao homologado")


def energy_rate(hour: int, solar_kw: float) -> tuple[float, str]:
    if 18 <= hour < 22:
        return 1.32, "ponta"
    if solar_kw >= 20 and 10 <= hour < 16:
        return 0.62, "solar"
    return 0.88, "fora de ponta"


def allocate_power(chargers: list[Charger], available_kw: float) -> list[Allocation]:
    active = [charger for charger in chargers if charger.connected and charger.requested_kw > 0]
    remaining = max(0.0, available_kw)
    assigned = {charger.charger_id: 0.0 for charger in active}
    pending = active[:]

    while pending and remaining > 0.001:
        total_weight = sum(charger.priority_weight * charger.urgency_weight for charger in pending)
        completed = []
        distributed = 0.0
        for charger in pending:
            weight = charger.priority_weight * charger.urgency_weight
            fair_share = remaining * weight / total_weight
            needed = charger.requested_kw - assigned[charger.charger_id]
            grant = min(fair_share, needed)
            assigned[charger.charger_id] += grant
            distributed += grant
            if needed - grant <= 0.001:
                completed.append(charger)
        remaining -= distributed
        pending = [charger for charger in pending if charger not in completed]
        if distributed <= 0.001:
            break

    results = []
    for charger in chargers:
        allocated = round(assigned.get(charger.charger_id, 0.0), 2)
        if not charger.connected:
            status = "desconectado"
        elif allocated <= 0:
            status = "aguardando"
        elif allocated + 0.01 < charger.requested_kw:
            status = "limitado pelo DLM"
        else:
            status = "carga nominal"
        results.append(
            Allocation(
                charger_id=charger.charger_id,
                protocol_received=charger.protocol,
                normalized_protocol=normalize_protocol(charger.protocol),
                requested_kw=charger.requested_kw,
                allocated_kw=allocated,
                battery_pct=charger.battery_pct,
                priority=charger.priority,
                status=status,
            )
        )
    return results


def simulate(payload: dict) -> dict:
    contract_kw = max(0.0, float(payload.get("contract_kw", 150)))
    building_kw = max(0.0, float(payload.get("building_kw", 75)))
    solar_kw = max(0.0, float(payload.get("solar_kw", 20)))
    bess_kw = max(0.0, float(payload.get("bess_kw", 0)))
    hour = int(payload.get("hour", 14)) % 24
    duration_hours = max(0.0, float(payload.get("duration_hours", 1)))

    chargers = [
        Charger(
            charger_id=str(item.get("charger_id", f"CP-{index + 1:02d}")),
            protocol=str(item.get("protocol", "OCPP 1.6")),
            requested_kw=max(0.0, float(item.get("requested_kw", 7.4))),
            battery_pct=min(100.0, max(0.0, float(item.get("battery_pct", 50)))),
            priority=str(item.get("priority", "normal")),
            connected=bool(item.get("connected", True)),
        )
        for index, item in enumerate(payload.get("chargers", []))
    ]

    grid_margin_kw = max(0.0, contract_kw - building_kw)
    available_kw = grid_margin_kw + solar_kw + bess_kw
    allocations = allocate_power(chargers, available_kw)
    requested_total = sum(charger.requested_kw for charger in chargers if charger.connected)
    allocated_total = sum(item.allocated_kw for item in allocations)
    rate, tariff_name = energy_rate(hour, solar_kw)
    energy_kwh = allocated_total * duration_hours
    session_revenue = energy_kwh * rate
    avoided_overload_kw = max(0.0, building_kw + requested_total - solar_kw - bess_kw - contract_kw)

    predictor = DemandPredictor()
    weekday = int(payload.get("weekday", 2)) % 7
    temperature_c = float(payload.get("temperature_c", 25))
    event = bool(payload.get("event", False))
    forecast = predictor.day_forecast(weekday, temperature_c, event)

    return {
        "summary": {
            "contract_kw": round(contract_kw, 2),
            "available_for_charging_kw": round(available_kw, 2),
            "requested_kw": round(requested_total, 2),
            "allocated_kw": round(allocated_total, 2),
            "avoided_overload_kw": round(avoided_overload_kw, 2),
            "utilization_pct": round(100 * allocated_total / available_kw, 1) if available_kw else 0,
            "energy_kwh": round(energy_kwh, 2),
            "tariff": tariff_name,
            "rate_brl_kwh": rate,
            "estimated_revenue_brl": round(session_revenue, 2),
        },
        "allocations": [item.to_dict() for item in allocations],
        "forecast": forecast,
        "alerts": _alerts(contract_kw, building_kw, requested_total, solar_kw, bess_kw, allocations),
    }


def _alerts(contract_kw, building_kw, requested_kw, solar_kw, bess_kw, allocations) -> list[dict]:
    alerts = []
    raw_grid_demand = building_kw + requested_kw - solar_kw - bess_kw
    if raw_grid_demand > contract_kw:
        alerts.append(
            {
                "level": "warning",
                "message": f"DLM evitou ultrapassagem de {raw_grid_demand - contract_kw:.1f} kW.",
            }
        )
    incompatible = [
        item.charger_id
        for item in allocations
        if item.normalized_protocol == "Protocolo nao homologado"
    ]
    if incompatible:
        alerts.append(
            {
                "level": "error",
                "message": "Revisar protocolo dos carregadores: " + ", ".join(incompatible),
            }
        )
    if not alerts:
        alerts.append({"level": "success", "message": "Operacao dentro dos limites configurados."})
    return alerts


def default_payload() -> dict:
    return {
        "contract_kw": 150,
        "building_kw": 115,
        "solar_kw": 18,
        "bess_kw": 10,
        "hour": 19,
        "duration_hours": 1.5,
        "weekday": 2,
        "temperature_c": 27,
        "event": False,
        "chargers": [
            {"charger_id": "CP-01", "protocol": "OCPP 1.6", "requested_kw": 22, "battery_pct": 18, "priority": "frota"},
            {"charger_id": "CP-02", "protocol": "OCPP 2.0.1", "requested_kw": 22, "battery_pct": 62, "priority": "normal"},
            {"charger_id": "CP-03", "protocol": "OCPP 1.5", "requested_kw": 11, "battery_pct": 35, "priority": "premium"},
            {"charger_id": "CP-04", "protocol": "Proprietario", "requested_kw": 22, "battery_pct": 75, "priority": "normal"},
            {"charger_id": "CP-05", "protocol": "OCPP 1.6-J", "requested_kw": 7.4, "battery_pct": 12, "priority": "emergencia"},
        ],
    }
