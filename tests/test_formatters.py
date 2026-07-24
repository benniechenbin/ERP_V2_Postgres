import pandas as pd
import pytest

from backend.utils.formatters import parse_date_cell


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("2025-06-30", "2025-06-30"),
        ("2025.06.30", "2025-06-30"),
        ("2025/06/30", "2025-06-30"),
        ("2025年6月30日", "2025-06-30"),
        ("20250630", "2025-06-30"),
        ("2025.06", "2025-06-01"),
        ("2025年6月", "2025-06-01"),
        (pd.Timestamp("2025-06-30"), "2025-06-30"),
    ],
)
def test_parse_date_cell_supported_formats(value, expected):
    assert parse_date_cell(value) == expected


@pytest.mark.parametrize("value", [None, "", "年底", "2025-99-99"])
def test_parse_date_cell_invalid_values_return_none(value):
    assert parse_date_cell(value) is None
