"""Structured-output extraction with validation — Python's AI-layer strength.

Layer: research & data / structured extraction (Layer 1-2 of the guide's map).
Python owns the "unstructured in, trustworthy data out" pattern in AI:
a model (or, here, a deterministic local stand-in for one) proposes JSON,
and a typed schema decides whether that JSON is allowed into the rest of
the system. Validation uses pydantic when it is installed and falls back
to a stdlib dataclass implementation with the same checks when it is not,
so this file runs anywhere with zero installation and zero API keys.

Run:  python3 extract_invoice.py     (runs a tiny self-test, then a demo)
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field

# --------------------------------------------------------------------------
# The contract. Every field the downstream system depends on is named,
# typed, and constrained *before* any model output is trusted.
# --------------------------------------------------------------------------

try:
    from pydantic import BaseModel, Field, ValidationError

    class Invoice(BaseModel):
        vendor: str = Field(min_length=1)
        invoice_number: str = Field(min_length=1)
        total: float = Field(ge=0)
        currency: str = Field(pattern=r"^[A-Z]{3}$")
        due_date: str | None = None
        line_items: list[str] = Field(default_factory=list)

    def validate_invoice(data: dict) -> "Invoice":
        return Invoice(**data)

    BACKEND = "pydantic"

except ImportError:  # stdlib fallback: same contract, hand-rolled checks
    @dataclass
    class Invoice:  # type: ignore[no-redef]
        vendor: str
        invoice_number: str
        total: float
        currency: str
        due_date: str | None = None
        line_items: list[str] = field(default_factory=list)

    class ValidationError(ValueError):
        pass

    def validate_invoice(data: dict) -> "Invoice":
        if not isinstance(data, dict):
            raise ValidationError("invoice payload must be an object")
        vendor = data.get("vendor")
        number = data.get("invoice_number")
        total = data.get("total")
        currency = data.get("currency")
        if not isinstance(vendor, str) or not vendor:
            raise ValidationError("vendor must be a non-empty string")
        if not isinstance(number, str) or not number:
            raise ValidationError("invoice_number must be a non-empty string")
        if not isinstance(total, (int, float)) or isinstance(total, bool) or total < 0:
            raise ValidationError("total must be a number >= 0")
        if not isinstance(currency, str) or not re.fullmatch(r"[A-Z]{3}", currency):
            raise ValidationError("currency must be a 3-letter uppercase code")
        items = data.get("line_items", [])
        if not isinstance(items, list) or not all(isinstance(x, str) for x in items):
            raise ValidationError("line_items must be a list of strings")
        due = data.get("due_date")
        if due is not None and not isinstance(due, str):
            raise ValidationError("due_date must be a string or null")
        return Invoice(vendor=vendor, invoice_number=number, total=float(total),
                       currency=currency, due_date=due, line_items=items)

    BACKEND = "dataclasses (stdlib fallback)"


# --------------------------------------------------------------------------
# A local, deterministic stand-in for an LLM extraction call.
# In production this is where the model API call goes; the point of the
# example is everything *around* it, which does not change.
# --------------------------------------------------------------------------

RAW_DOCUMENT = """
INVOICE  INV-2026-0142
From: Northwind Office Supplies
Items: A4 paper x10, toner cartridge x2
Total due: $184.50 USD
Pay by: 2026-12-01
"""


def fake_model_extract(document: str) -> dict:
    """Pretend-LLM: pulls fields out of the raw document as untrusted JSON."""
    def grab(pattern, default=None):
        m = re.search(pattern, document)
        return m.group(1) if m else default

    return {
        "vendor": grab(r"From:\s*(.+)", "unknown"),
        "invoice_number": grab(r"INVOICE\s+(\S+)", "unknown"),
        "total": float(grab(r"Total due:\s*\$([\d.]+)", "0")),
        "currency": grab(r"\$\d[\d.]*\s*([A-Z]{3})", "USD"),
        "due_date": grab(r"Pay by:\s*(\d{4}-\d{2}-\d{2})"),
        "line_items": [s.strip() for s in grab(r"Items:\s*(.+)", "").split(",") if s.strip()],
    }


def extract(document: str) -> Invoice:
    proposed: dict = fake_model_extract(document)   # untrusted
    return validate_invoice(proposed)               # trusted, or an exception


# --------------------------------------------------------------------------
# Tiny self-test: the contract must accept the good payload and reject
# the three classic model failure modes (wrong type, negative money,
# malformed currency).
# --------------------------------------------------------------------------

def self_test() -> None:
    good = extract(RAW_DOCUMENT)
    assert good.vendor == "Northwind Office Supplies"
    assert good.invoice_number == "INV-2026-0142"
    assert good.total == 184.50
    assert good.currency == "USD"
    bad_payloads = [
        {"vendor": "X", "invoice_number": "1", "total": "lots", "currency": "USD"},
        {"vendor": "X", "invoice_number": "1", "total": -5, "currency": "USD"},
        {"vendor": "X", "invoice_number": "1", "total": 5, "currency": "dollars"},
    ]
    for payload in bad_payloads:
        try:
            validate_invoice(payload)
        except ValidationError:
            continue
        raise AssertionError(f"bad payload was accepted: {payload}")
    print(f"self-test PASS (validation backend: {BACKEND})")


if __name__ == "__main__":
    self_test()
    invoice = extract(RAW_DOCUMENT)
    print(json.dumps(invoice.__dict__, indent=2))
    sys.exit(0)
