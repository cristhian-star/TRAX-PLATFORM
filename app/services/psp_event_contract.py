import re
from dataclasses import dataclass
from datetime import datetime


_SHA256_HEX = re.compile(r"[0-9a-fA-F]{64}")


def normalize_psp_provider(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError("provider must be a non-empty string")
    return value.strip().lower()


@dataclass(frozen=True, slots=True)
class PSPEvent:
    provider: str
    external_event_id: str
    topic: str
    action: str
    external_resource_id: str
    test_mode: bool
    occurred_at: datetime | None
    received_at: datetime
    payload_hash: str

    def __post_init__(self):
        object.__setattr__(self, "provider", normalize_psp_provider(self.provider))
        for name in (
            "external_event_id", "topic", "action",
            "external_resource_id",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        if type(self.test_mode) is not bool:
            raise ValueError("test_mode must be a boolean")
        for name in ("occurred_at", "received_at"):
            value = getattr(self, name)
            if value is None and name == "occurred_at":
                continue
            if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
                raise ValueError(f"{name} must be timezone-aware")
        if not isinstance(self.payload_hash, str) or _SHA256_HEX.fullmatch(self.payload_hash) is None:
            raise ValueError("payload_hash must be a 64-character SHA-256 hexadecimal value")
        object.__setattr__(self, "payload_hash", self.payload_hash.lower())
