"""
loader.py – Data loader for Siteworks.

Loads scoring data **only** from `data/Data_Center_Site_Selector_RH.xlsx`
(multisheet layout documented in `parser.py`). There is no built-in fallback.
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple

from src.data.schema import CityData
from src.data.parser import parse_rh_workbook

# Path where the RH workbook is expected
_WORKBOOK_PATH = Path(__file__).parent.parent.parent / "data" / "Data_Center_Site_Selector_RH.xlsx"


def load_city_data() -> Tuple[
    Dict[str, CityData],
    List[str],
    bool,
    Optional[Dict[str, float]],
    Optional[Dict[str, List[Tuple[str, str]]]],
]:
    """
    Load city scoring data from the Excel workbook.

    Returns:
        (city_data_map, quality_notes, from_workbook, workbook_weights, workbook_sources)
        - **from_workbook** is True only when at least one city was parsed successfully.
        - **workbook_weights** is set when the **Account Weights** sheet was read (may be None).
        - **workbook_sources** maps subcategory keys to [(city, url), …] from **Sources**, or None.
    """
    if not _WORKBOOK_PATH.is_file():
        notes = [
            f"❌ Required workbook not found: `{_WORKBOOK_PATH.name}`",
            f"Place the file in `{_WORKBOOK_PATH.parent}` and click **Refresh data** in the sidebar.",
        ]
        return {}, notes, False, None, None

    parsed, wb_weights, wb_sources = parse_rh_workbook(_WORKBOOK_PATH)
    if not parsed or len(parsed) < 1:
        notes = [
            f"❌ Could not read scoring data from `{_WORKBOOK_PATH.name}`.",
            "Confirm the **Scores** sheet exists with City / Name columns and numeric scores, "
            "or use **Refresh data** after fixing the file.",
        ]
        return {}, notes, False, None, None

    notes = _collect_quality_notes(parsed)
    notes.insert(0, f"✅ Loaded from workbook: {_WORKBOOK_PATH.name}")
    if wb_weights:
        notes.insert(
            1,
            "Category weights taken from the **Account Weights** worksheet.",
        )
    if wb_sources:
        idx = 2 if wb_weights else 1
        notes.insert(
            idx,
            "Per-metric citations read from the **Sources** worksheet.",
        )

    if len(parsed) < 3:
        notes.append(
            f"⚠️ Only **{len(parsed)}** cities loaded — add more rows to **Scores** for full comparison."
        )
    return parsed, notes, True, wb_weights, wb_sources


def _collect_quality_notes(city_data: Dict[str, CityData]) -> List[str]:
    """Aggregate data quality notes from parsed city data."""
    notes: List[str] = []
    for city, cd in city_data.items():
        for note in cd.data_quality_notes:
            notes.append(f"{city}: {note}")
    if not notes:
        notes.append("No data quality issues detected in workbook.")
    return notes
