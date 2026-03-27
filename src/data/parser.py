"""
parser.py – Excel workbook ingestion for Siteworks.

PARSING ASSUMPTIONS (documented here per project spec):
========================================================
1. The primary data source is `Data_Center_Site_Selector_RH.xlsx`,
   specifically the sheet named "Site Selector Data - edited".
2. City names appear in row 1 (header row) in columns B onward.
3. Subcategory names appear in column A.
4. Score cells contain numeric values in the 1–5 range.
5. If a score cell is blank or non-numeric it is treated as missing (None).
6. The workbook may contain extra sheets; only "Site Selector Data - edited"
   is parsed for scores.
7. Raw measurement values (e.g., "47 inches/year") may appear in adjacent
   cells; if present they are stored in SubcategoryScore.raw_value.
8. The file `CIVE 580 Project MAA.xlsx` is treated as a future-expansion
   template and is NOT parsed in this release.

If the workbook is absent or unreadable the loader falls back to the
built-in pilot dataset defined in loader.py.
"""

import logging
from pathlib import Path
from typing import Dict, Optional, Tuple

from src.data.schema import (
    SUBCATEGORIES,
    PILOT_CITIES,
    SubcategoryScore,
    CityData,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Public parse entry point
# ---------------------------------------------------------------------------

def parse_rh_workbook(path: Path) -> Optional[Dict[str, CityData]]:
    """
    Parse `Data_Center_Site_Selector_RH.xlsx` and return a city → CityData map.

    Returns None if openpyxl is unavailable or the file cannot be read.
    Partial data (some scores missing) is returned with quality notes rather
    than raising an exception.
    """
    try:
        import openpyxl  # noqa: PLC0415  (optional dependency)
    except ImportError:
        logger.warning("openpyxl not installed – falling back to built-in data.")
        return None

    if not path.is_file():
        logger.info("Workbook not found at %s – using built-in data.", path)
        return None

    try:
        wb = openpyxl.load_workbook(path, data_only=True)
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to open workbook %s: %s", path, exc)
        return None

    sheet = _find_sheet(wb)
    if sheet is None:
        logger.warning("Could not locate 'Site Selector Data - edited' sheet.")
        return None

    return _extract_scores(sheet)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _find_sheet(wb):
    """Return the target worksheet, trying several likely names."""
    candidates = [
        "Site Selector Data - edited",
        "Site Selector Data",
        "SiteSelector",
        "Data",
        "Sheet1",
    ]
    for name in candidates:
        if name in wb.sheetnames:
            return wb[name]
    # Fall back to first sheet
    if wb.sheetnames:
        logger.warning(
            "Target sheet not found; falling back to first sheet: %s",
            wb.sheetnames[0],
        )
        return wb[wb.sheetnames[0]]
    return None


def _extract_scores(sheet) -> Dict[str, CityData]:
    """
    Extract city × subcategory score matrix from the worksheet.

    Expected layout:
        Row 1 : headers – col A = label, col B+ = city names
        Row 2+: data   – col A = subcategory name, col B+ = score values
    """
    # Read header row to find city columns
    header_row = list(sheet.iter_rows(min_row=1, max_row=1, values_only=True))[0]
    city_col_map: Dict[str, int] = {}  # city_name → 0-based col index
    for col_idx, cell_val in enumerate(header_row):
        if col_idx == 0:
            continue
        if cell_val:
            cell_str = str(cell_val).strip()
            # Match against known pilot city names (case-insensitive)
            matched = _match_city(cell_str)
            if matched:
                city_col_map[matched] = col_idx

    if not city_col_map:
        logger.warning("No pilot cities found in workbook header row.")
        return {}

    # Build subcategory name → canonical name mapping
    all_subs = {
        sub: sub
        for subs in SUBCATEGORIES.values()
        for sub in subs
    }

    # Initialise CityData containers
    city_data: Dict[str, CityData] = {
        city: CityData(name=city) for city in city_col_map
    }

    # Read data rows
    for row in sheet.iter_rows(min_row=2, values_only=True):
        if not row or row[0] is None:
            continue
        row_label = str(row[0]).strip()
        canonical = _match_subcategory(row_label, all_subs)
        if canonical is None:
            continue

        for city, col_idx in city_col_map.items():
            raw_val = row[col_idx] if col_idx < len(row) else None
            score = _parse_score(raw_val)
            city_data[city].subcategory_scores[canonical] = SubcategoryScore(
                name=canonical,
                score=score if score is not None else float("nan"),
                raw_value=str(raw_val) if raw_val is not None else None,
                note="Parsed from workbook" if score is not None else "Missing/blank",
            )
            if score is None:
                city_data[city].data_quality_notes.append(
                    f"Missing score for '{canonical}'"
                )

    return city_data


def _match_city(cell_str: str) -> Optional[str]:
    """Fuzzy-match a cell string to a known pilot city name."""
    cell_lower = cell_str.lower()
    for city in PILOT_CITIES:
        if city.lower() in cell_lower or cell_lower in city.lower():
            return city
    return None


def _match_subcategory(label: str, mapping: Dict[str, str]) -> Optional[str]:
    """Fuzzy-match a row label to a canonical subcategory name."""
    label_lower = label.lower().strip()
    for canonical in mapping:
        if canonical.lower() == label_lower:
            return canonical
        # Allow partial match (at least 70% of words)
        canonical_words = set(canonical.lower().split())
        label_words = set(label_lower.split())
        if canonical_words and label_words:
            overlap = canonical_words & label_words
            if len(overlap) / len(canonical_words) >= 0.7:
                return canonical
    return None


def _parse_score(value) -> Optional[float]:
    """Convert a cell value to a float score, or None if invalid."""
    if value is None:
        return None
    try:
        f = float(value)
        if 0 <= f <= 5:
            return f
        # Some workbooks store raw ranks (1=best) – invert if > 5
        if 1 <= f <= 10:
            return round(6 - (f / 2), 2)  # normalise to 1–5
        return None
    except (TypeError, ValueError):
        return None
