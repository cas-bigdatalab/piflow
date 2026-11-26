"""Lossless numeric input repair; the caller still validates the full schema."""
from decimal import Decimal, InvalidOperation
import math
import re


def _types(schema):
    if not isinstance(schema, dict):
        return set()
    kind = schema.get("type")
    if kind is not None:
        return {kind} if isinstance(kind, str) else set(kind)
    for key in ("anyOf", "oneOf"):
        if key in schema:
            branches = [_types(child) for child in schema[key]]
            if branches and all(branches):
                return set().union(*branches)
    return set()


def normalize_numbers(value, schema):
    """Repair explicit numeric fields without guessing strings, IDs or defaults.

    Leave reference-only and ambiguous union schemas to their validator. Keep
    unknown fields and every constraint; no mutation occurs until validation.
    """
    if not isinstance(schema, dict):
        return value
    if isinstance(value, dict):
        properties = schema.get("properties", {})
        return {key: normalize_numbers(child, properties.get(key)) for key, child in value.items()}
    if isinstance(value, list):
        prefix = schema.get("prefixItems", [])
        return [normalize_numbers(child, prefix[index] if index < len(prefix) else schema.get("items"))
            for index, child in enumerate(value)]
    kinds = _types(schema)
    if not isinstance(value, str) or not kinds or not kinds <= {"integer", "number", "null"}:
        return value
    raw = value.strip()
    # Preserve zero-padded identifiers and reject non-finite/locale-dependent
    # spellings. Bounds prevent pathological exponent expansion during repair.
    if len(raw) > 128 or not re.fullmatch(r"-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?", raw):
        return value
    try:
        number = Decimal(raw)
        if not number.is_finite() or abs(number.adjusted()) > 308:
            return value
        if kinds & {"integer", "number"} and number == number.to_integral_value():
            return int(number)
        if "number" in kinds:
            result = float(number)
            if math.isfinite(result) and Decimal(str(result)) == number:
                return result
    except (InvalidOperation, OverflowError, ValueError):
        pass
    return value
