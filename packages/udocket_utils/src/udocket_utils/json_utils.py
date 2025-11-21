# Copyright (c) 2025 uDocket. All Rights Reserved.
#
# PROPRIETARY AND CONFIDENTIAL
#
# This software is the confidential and proprietary information of uDocket.
# You shall not disclose such confidential information and shall use it only
# in accordance with the terms of the license agreement you entered into with uDocket.
"""Typed helpers for working with JSON data structures."""

from __future__ import annotations

import json
from collections.abc import Callable, Iterable, Mapping, Sequence
from typing import TYPE_CHECKING, TypeGuard, TypeVar, cast

if TYPE_CHECKING:
    from pathlib import Path

type JSONPrimitive = str | int | float | bool | None
type JSONValue = JSONPrimitive | JSONObject | JSONArray
type JSONObject = dict[str, JSONValue]
type JSONArray = list[JSONValue]

KeyT = TypeVar("KeyT")
ValueT = TypeVar("ValueT")
ResultT = TypeVar("ResultT")


def is_json_scalar(value: object) -> TypeGuard[JSONPrimitive]:
    """Return ``True`` when *value* is a valid JSON scalar.

    Args:
        value: Arbitrary Python object to evaluate.

    Returns:
        TypeGuard[JSONPrimitive]: ``True`` when ``value`` is a JSON scalar, ``False`` otherwise.
    """
    return isinstance(value, (str, int, float, bool)) or value is None


def coerce_json_value(value: object) -> JSONValue:
    """Convert ``value`` into a JSON-compatible representation.

    Args:
        value: Arbitrary Python value to convert.

    Returns:
        JSONValue: JSON-compatible data representing ``value``.
    """
    if is_json_scalar(value):
        return value
    if isinstance(value, Mapping):
        mapping_value = cast("Mapping[object, object]", value)
        return {str(key): coerce_json_value(item) for key, item in mapping_value.items()}
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        sequence_value = cast("Sequence[object]", value)
        return [coerce_json_value(item) for item in sequence_value]
    return str(value)


def json_payload(**items: object) -> JSONObject:
    """Build a JSON object from keyword arguments.

    Returns:
        JSONObject: JSON object containing coerced values.
    """
    return {key: coerce_json_value(value) for key, value in items.items()}


def coerce_json_object(value: object, *, default: JSONObject | None = None) -> JSONObject:
    """Coerce *value* into a ``JSONObject``.

    Args:
        value: Candidate mapping to convert.
        default: Optional fallback returned when ``value`` is not a mapping.

    Returns:
        JSONObject: JSON object.
    """
    if isinstance(value, Mapping):
        mapping_value = cast("Mapping[object, object]", value)
        return {str(key): coerce_json_value(item) for key, item in mapping_value.items()}
    return {} if default is None else dict(default)


def merge_json_objects(*objects: object) -> JSONObject:
    """Merge JSON-mappable objects into a single dictionary.

    Args:
        *objects: Candidate mappings or mapping-like objects whose contents
            should be merged.

    Returns:
        JSONObject: Combined dictionary containing the union of provided keys.
    """
    merged: JSONObject = {}
    for candidate in objects:
        if not isinstance(candidate, Mapping):
            continue
        mapping_value = cast("Mapping[object, object]", candidate)
        for key, raw_value in mapping_value.items():
            merged[str(key)] = coerce_json_value(raw_value)
    return merged


def json_object_to_dict(payload: JSONObject) -> dict[str, JSONValue]:
    """Return a shallow copy of ``payload``.

    Args:
        payload: JSON object to copy.

    Returns:
        dict[str, JSONValue]: Copy of ``payload``.
    """
    return dict(payload)


def normalize_mapping(
    mapping: Mapping[KeyT, ValueT],
    *,
    transform: Callable[[ValueT], ResultT] | None = None,
) -> dict[str, ValueT] | dict[str, ResultT]:
    """Normalize a mapping by converting keys to strings.

    Args:
        mapping: Mapping to normalize.
        transform: Optional callback applied to each value.

    Returns:
        dict[str, ValueT | ResultT]: Normalized mapping with string keys.
    """
    if transform is None:
        return {str(key): value for key, value in mapping.items()}
    return {str(key): transform(value) for key, value in mapping.items()}


def normalize_mapping_optional(
    value: Mapping[KeyT, ValueT] | object,
    *,
    transform: Callable[[ValueT], ResultT] | None = None,
) -> dict[str, ValueT] | dict[str, ResultT]:
    """Normalize mappings while gracefully handling non-mapping inputs.

    Args:
        value: Candidate mapping to normalize.
        transform: Optional callback applied to each value.

    Returns:
        dict[str, ValueT | ResultT]: Normalized dictionary or ``{}`` when
        ``value`` is not a mapping.
    """
    if not isinstance(value, Mapping):
        return {}
    normalized = cast("Mapping[object, ValueT]", value)
    if transform is None:
        return {str(key): value_item for key, value_item in normalized.items()}
    return {str(key): transform(item) for key, item in normalized.items()}


def coerce_object_dict(
    value: object,
    *,
    key_transform: Callable[[str], str] | None = None,
    drop_empty_keys: bool = False,
    drop_none_values: bool = False,
) -> dict[str, JSONValue]:
    """Coerce a mapping into ``dict[str, JSONValue]``.

    Args:
        value: Candidate mapping to normalize.
        key_transform: Optional key transformation function.
        drop_empty_keys: When ``True`` empty keys are ignored.
        drop_none_values: When ``True`` entries with ``None`` values are
            discarded.

    Returns:
        dict[str, JSONValue]: Normalized dictionary.
    """
    base = cast("dict[str, object]", normalize_mapping_optional(value))

    def identity(text: str) -> str:
        """Return ``text`` unchanged (default key transformer).

        Args:
            text: Key to normalize.

        Returns:
            str: The same key that was provided.
        """
        return text

    transform: Callable[[str], str] = key_transform or identity
    result: dict[str, JSONValue] = {}
    for raw_key, raw_value in base.items():
        key = transform(raw_key)
        if drop_empty_keys and not key:
            continue
        if drop_none_values and raw_value is None:
            continue
        result[key] = coerce_json_value(raw_value)
    return result


def normalize_json_object(
    value: object,
    *,
    strip_keys: bool = True,
    drop_empty_keys: bool = False,
    drop_nullish_values: bool = False,
) -> JSONObject:
    """Normalize keys/values of a JSON object while optionally dropping entries.

    Args:
        value: Candidate JSON object.
        strip_keys: Remove surrounding whitespace from keys.
        drop_empty_keys: Discard keys that become empty after stripping.
        drop_nullish_values: Drop ``None`` or empty values.

    Returns:
        JSONObject: Normalized object.
    """
    payload = coerce_json_object(value)
    result: JSONObject = {}
    for key, raw in payload.items():
        normalized_key = key.strip() if strip_keys else key
        if drop_empty_keys and not normalized_key:
            continue
        if drop_nullish_values:
            if raw is None:
                continue
            if isinstance(raw, (str, bytes)) and not raw:
                continue
            if isinstance(raw, (list, dict)) and not raw:
                continue
        result[normalized_key] = raw
    return result


def ensure_json_object(value: object, *, context: str | None = None) -> JSONObject:
    """Validate that *value* is a mapping and coerce it into a JSON object.

    Args:
        value: Candidate mapping.
        context: Optional label used in error messages.

    Returns:
        JSONObject: JSON object derived from ``value``.

    Raises:
        TypeError: If ``value`` is not a mapping.
    """
    if not isinstance(value, Mapping):
        label = context or "mapping"
        message = f"Expected mapping for {label}, received {type(value)!r}"
        raise TypeError(message)
    mapping_value = cast("Mapping[object, object]", value)
    return {str(key): coerce_json_value(item) for key, item in mapping_value.items()}


def coerce_json_array(value: object) -> JSONArray:
    """Coerce an iterable into a JSON array.

    Args:
        value: Candidate sequence.

    Returns:
        JSONArray: JSON array containing normalized values.
    """
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        sequence_value = cast("Sequence[object]", value)
        return [coerce_json_value(item) for item in sequence_value]
    return []


def coerce_object_list(value: object) -> list[JSONObject]:
    """Return list of JSON objects from a sequence of mappings.

    Args:
        value: Candidate sequence of mapping objects.

    Returns:
        list[JSONObject]: Sequence of JSON objects.
    """
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        sequence_value = cast("Sequence[object]", value)
        return [
            coerce_json_object(cast("Mapping[object, object]", item))
            for item in sequence_value
            if isinstance(item, Mapping)
        ]
    return []


def coerce_str_dict(
    value: object,
    *,
    drop_empty: bool = True,
    value_drop_empty: bool = True,
    lower_keys: bool = False,
) -> dict[str, str]:
    """Coerce a mapping into ``dict[str, str]`` with filtering options.

    Args:
        value: Candidate mapping.
        drop_empty: Drop entries with empty keys.
        value_drop_empty: Drop entries with empty values.
        lower_keys: Convert keys to lowercase.

    Returns:
        dict[str, str]: Normalized dictionary.
    """
    if not isinstance(value, Mapping):
        return {}
    mapping_value = cast("Mapping[object, object]", value)
    result: dict[str, str] = {}
    for key, raw in mapping_value.items():
        normalized_key = str(key).strip()
        if lower_keys:
            normalized_key = normalized_key.lower()
        if drop_empty and not normalized_key:
            continue
        normalized_value = coerce_str(raw)
        if value_drop_empty and not normalized_value:
            continue
        if normalized_value is not None:
            result[normalized_key] = normalized_value
    return result


def coerce_str(value: object) -> str | None:
    """Convert a value to a trimmed string or ``None`` if empty.

    Args:
        value: Candidate value.

    Returns:
        str | None: Trimmed string or ``None``.
    """
    if value is None:
        return None
    if isinstance(value, str):
        stripped = value.strip()
        return stripped or None
    text = str(value).strip()
    return text or None


def coerce_str_list(
    value: object,
    *,
    unique: bool = True,
    drop_empty: bool = True,
    lower: bool = False,
) -> list[str]:
    """Coerce an iterable into a list of normalized strings.

    Args:
        value: Iterable of candidate values.
        unique: Ensure unique entries when ``True``.
        drop_empty: Discard empty entries.
        lower: Normalize values to lowercase when ``True``.

    Returns:
        list[str]: Normalized list.
    """
    if isinstance(value, str):
        items: list[str] = [value]
    elif isinstance(value, Iterable):
        iterable_value = cast("Iterable[object]", value)
        items = [str(item) for item in iterable_value if item is not None]
    else:
        return []
    normalized: list[str] = []
    seen: set[str] = set()
    for item in items:
        candidate = item.strip()
        if lower:
            candidate = candidate.lower()
        if drop_empty and not candidate:
            continue
        if unique:
            if candidate in seen:
                continue
            seen.add(candidate)
        normalized.append(candidate)
    return normalized


def coerce_int(
    value: object,
    *,
    default: int | None = None,
    minimum: int | None = None,
    maximum: int | None = None,
) -> int | None:
    """Coerce a value to an int, enforcing optional bounds.

    Args:
        value: Candidate value to coerce.
        default: Fallback when coercion fails.
        minimum: Optional lower bound.
        maximum: Optional upper bound.

    Returns:
        int | None: Normalized integer or ``None``.
    """
    candidate: int | None
    if isinstance(value, bool):
        candidate = int(value)
    elif isinstance(value, int):
        candidate = value
    elif isinstance(value, float):
        candidate = int(value)
    elif isinstance(value, str):
        try:
            candidate = int(value.strip())
        except ValueError:
            candidate = default
    else:
        candidate = default
    if candidate is None:
        return None
    result = candidate
    if minimum is not None and result < minimum:
        result = minimum
    if maximum is not None and result > maximum:
        result = maximum
    return result


def coerce_float(
    value: object,
    *,
    default: float | None = None,
    minimum: float | None = None,
    maximum: float | None = None,
) -> float | None:
    """Coerce a value to a float, enforcing optional bounds.

    Args:
        value: Candidate value to coerce.
        default: Fallback when coercion fails.
        minimum: Optional lower bound.
        maximum: Optional upper bound.

    Returns:
        float | None: Normalized float or ``None`` when coercion fails.
    """
    candidate: float | None
    if isinstance(value, (bool, int, float)):
        candidate = float(value)
    elif isinstance(value, str):
        try:
            candidate = float(value.strip())
        except ValueError:
            candidate = default
    else:
        candidate = default
    if candidate is None:
        return None
    result = candidate
    if minimum is not None and result < minimum:
        result = minimum
    if maximum is not None and result > maximum:
        result = maximum
    return result


def coerce_bool(value: object, *, default: bool | None = None) -> bool | None:
    """Coerce a value into a boolean using common string representations.

    Args:
        value: Candidate value.
        default: Fallback result when coercion fails.

    Returns:
        bool | None: Normalized boolean or ``None``.
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return bool(value)
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "1", "yes", "y", "on"}:
            return True
        if lowered in {"false", "0", "no", "n", "off"}:
            return False
    return default


def read_json_value(path: Path) -> JSONValue | None:
    """Read a JSON file and return the value, or ``None`` on failure.

    Args:
        path: File to read.

    Returns:
        JSONValue | None: Parsed JSON value or ``None`` when loading fails.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    try:
        raw = json.loads(text)
    except json.JSONDecodeError:
        return None
    return coerce_json_value(raw)


def read_json_object(path: Path, *, default: JSONObject | None = None) -> JSONObject:
    """Read a JSON file and return a dict, falling back to the provided default.

    Args:
        path: File to read.
        default: Optional fallback dictionary.

    Returns:
        JSONObject: Parsed JSON object.
    """
    value = read_json_value(path)
    if isinstance(value, dict):
        return value
    return {} if default is None else dict(default)


def write_json_object(
    path: Path,
    payload: Mapping[str, object],
    *,
    indent: int = 2,
) -> None:
    """Write a mapping to disk as JSON.

    Args:
        path: Destination path.
        payload: Mapping to serialize.
        indent: Pretty-print indentation.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized: JSONObject = {str(key): coerce_json_value(value) for key, value in payload.items()}
    path.write_text(
        json.dumps(normalized, ensure_ascii=False, indent=indent),
        encoding="utf-8",
    )


def parse_json_value(data: str) -> JSONValue | None:
    """Parse JSON text into a JSONValue, returning ``None`` on error.

    Args:
        data: JSON string to parse.

    Returns:
        JSONValue | None: Parsed JSON value or ``None`` on failure.
    """
    try:
        raw = json.loads(data)
    except json.JSONDecodeError:
        return None
    return coerce_json_value(raw)


def parse_json_value_strict(data: str, *, context: str | None = None) -> JSONValue:
    """Parse JSON text into a JSONValue, raising ``ValueError`` on error.

    Args:
        data: JSON string to parse.
        context: Optional label used in error messages.

    Returns:
        JSONValue: Parsed JSON data.

    Raises:
        ValueError: If ``data`` cannot be parsed as JSON.
    """
    try:
        raw = json.loads(data)
    except json.JSONDecodeError as exc:
        label = context or "JSON payload"
        message = f"Invalid {label}: {exc}"
        raise ValueError(message) from exc
    return coerce_json_value(raw)


def parse_json_object(data: str, *, context: str | None = None) -> JSONObject:
    """Parse JSON text into a JSONObject, enforcing object shape.

    Args:
        data: JSON string to parse.
        context: Optional label used in error messages.

    Returns:
        JSONObject: Parsed JSON object.

    Raises:
        TypeError: If the payload is not a JSON object.
    """
    value = parse_json_value_strict(data, context=context)
    if not isinstance(value, dict):
        label = context or "JSON payload"
        message = f"Expected JSON object for {label}"
        raise TypeError(message)
    return value


def load_json_object(path: Path, *, context: str | None = None) -> JSONObject:
    """Load a JSON object from disk, raising ``ValueError`` on failure.

    Args:
        path: File path to read.
        context: Optional label used in error messages.

    Returns:
        JSONObject: Parsed JSON object.

    Raises:
        ValueError: If the file cannot be read or does not contain a JSON object.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        label = context or str(path)
        message = f"Unable to read JSON file {label}: {exc}"
        raise ValueError(message) from exc
    label = context or str(path)
    return parse_json_object(text, context=label)


def load_json_value(path: Path, *, context: str | None = None) -> JSONValue:
    """Load arbitrary JSON data from disk, raising ``ValueError`` on failure.

    Args:
        path: File path to read.
        context: Optional label used in error messages.

    Returns:
        JSONValue: Parsed JSON data.

    Raises:
        ValueError: If the file cannot be read or contains invalid JSON.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        label = context or str(path)
        message = f"Unable to read JSON file {label}: {exc}"
        raise ValueError(message) from exc
    label = context or str(path)
    return parse_json_value_strict(text, context=label)


def write_json_value(
    path: Path,
    value: JSONValue,
    *,
    indent: int = 2,
) -> None:
    """Write a JSON-compatible value to disk.

    Args:
        path: Destination path.
        value: JSON value to serialize.
        indent: Pretty-print indentation.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    serialization = json.dumps(value, ensure_ascii=False, indent=indent)
    path.write_text(serialization, encoding="utf-8")


def stringify_json(value: object, *, indent: int | None = None, sort_keys: bool = False) -> str:
    """Return a JSON string for any object after coercion.

    Args:
        value: Value to serialize.
        indent: Optional indentation.
        sort_keys: Whether to sort dictionary keys.

    Returns:
        str: JSON string representation.
    """
    coerced = coerce_json_value(value)
    return json.dumps(coerced, ensure_ascii=False, indent=indent, sort_keys=sort_keys)


def stringify_pretty(value: object, *, sort_keys: bool = True) -> str:
    """Return a pretty-printed JSON string.

    Args:
        value: Value to serialize.
        sort_keys: Whether to sort dictionary keys.

    Returns:
        str: Pretty JSON string.
    """
    return stringify_json(value, indent=2, sort_keys=sort_keys)


__all__ = [
    "JSONArray",
    "JSONObject",
    "JSONPrimitive",
    "JSONValue",
    "coerce_bool",
    "coerce_float",
    "coerce_int",
    "coerce_json_array",
    "coerce_json_object",
    "coerce_json_value",
    "coerce_object_dict",
    "coerce_object_list",
    "coerce_str",
    "coerce_str_dict",
    "coerce_str_list",
    "ensure_json_object",
    "is_json_scalar",
    "json_object_to_dict",
    "json_payload",
    "load_json_object",
    "load_json_value",
    "merge_json_objects",
    "normalize_json_object",
    "normalize_mapping",
    "normalize_mapping_optional",
    "parse_json_object",
    "parse_json_value",
    "parse_json_value_strict",
    "read_json_object",
    "read_json_value",
    "stringify_json",
    "stringify_pretty",
    "write_json_object",
    "write_json_value",
]
