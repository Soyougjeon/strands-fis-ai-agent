"""Visualization service - Graph/Chart data conversion."""

from datetime import date, datetime


def detect_chart_data(raw_data: list[dict], columns: list[str]) -> dict | None:
    """Auto-detect chart type from SQL result and generate chart data.

    Rules (BR-07-02):
    - 2 columns (string + number) -> bar chart
    - date + number -> line chart
    - ratio data -> pie chart
    - Otherwise -> None (table only)
    """
    if not raw_data or len(columns) < 2:
        return None

    sample = raw_data[0]
    str_cols = []
    num_cols = []
    date_cols = []

    for col in columns:
        val = sample.get(col)
        if isinstance(val, (int, float)):
            num_cols.append(col)
        elif isinstance(val, (date, datetime)):
            date_cols.append(col)
        elif isinstance(val, str):
            # Check if string looks like a date
            try:
                datetime.fromisoformat(str(val).replace("Z", "+00:00"))
                date_cols.append(col)
            except (ValueError, TypeError):
                str_cols.append(col)
        else:
            str_cols.append(col)

    if not num_cols:
        return None

    # Date + Number -> line chart
    if date_cols and num_cols:
        return {
            "chart_type": "line",
            "title": "",
            "data": [{col: _serialize(row.get(col)) for col in columns} for row in raw_data],
            "x_axis": date_cols[0],
            "y_axis": num_cols[0],
        }

    # String + Number (2 columns) -> bar or pie
    if str_cols and num_cols and len(columns) <= 3:
        # Check if data looks like ratios (sum ~100)
        values = [row.get(num_cols[0], 0) for row in raw_data if isinstance(row.get(num_cols[0]), (int, float))]
        total = sum(values)
        is_ratio = 95 <= total <= 105 and len(values) >= 2

        return {
            "chart_type": "pie" if is_ratio else "bar",
            "title": "",
            "data": [{col: _serialize(row.get(col)) for col in columns} for row in raw_data],
            "x_axis": str_cols[0],
            "y_axis": num_cols[0],
        }

    return None


def _serialize(val):
    """Convert non-JSON-serializable values."""
    if isinstance(val, (date, datetime)):
        return val.isoformat()
    return val
