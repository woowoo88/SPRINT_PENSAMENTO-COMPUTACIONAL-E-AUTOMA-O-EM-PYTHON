from dataclasses import asdict, dataclass


PRIORITY_WEIGHTS = {
    "normal": 1.0,
    "premium": 1.35,
    "frota": 1.7,
    "emergencia": 2.2,
}


@dataclass(frozen=True)
class Charger:
    charger_id: str
    protocol: str
    requested_kw: float
    battery_pct: float
    priority: str = "normal"
    connected: bool = True

    @property
    def priority_weight(self) -> float:
        return PRIORITY_WEIGHTS.get(self.priority, 1.0)

    @property
    def urgency_weight(self) -> float:
        return 1.0 + max(0.0, 100.0 - self.battery_pct) / 100.0


@dataclass(frozen=True)
class Allocation:
    charger_id: str
    protocol_received: str
    normalized_protocol: str
    requested_kw: float
    allocated_kw: float
    battery_pct: float
    priority: str
    status: str

    def to_dict(self) -> dict:
        return asdict(self)

