from __future__ import annotations

import os
import re
from collections.abc import Mapping
from typing import Any, Protocol


REFERENCE_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]{2,127}$")
SENSITIVE_KEYS = re.compile(
    r"(password|passwd|secret|token|cookie|authorization|api[-_]?key|session)",
    re.IGNORECASE,
)


class CredentialProvider(Protocol):
    def get(self, credential_reference: str) -> str | None: ...


class EnvironmentCredentialProvider:
    def get(self, credential_reference: str) -> str | None:
        if not REFERENCE_PATTERN.fullmatch(credential_reference):
            raise ValueError("Credential references must be uppercase environment variable names")
        return os.getenv(credential_reference)


def redact(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            key: "[REDACTED]" if SENSITIVE_KEYS.search(str(key)) else redact(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact(item) for item in value]
    if isinstance(value, tuple):
        return tuple(redact(item) for item in value)
    return value
